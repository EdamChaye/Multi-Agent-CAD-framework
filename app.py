import streamlit as st
import asyncio
import os
import base64
import warnings

from src.config import DB_URI, STL_OUTPUT, OUTPUT_FOLDER


from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command
from src.graph import create_cad_graph

# --- EMPIRE STABILITY ---
warnings.filterwarnings("ignore")
st.set_page_config(page_title="Multi agent CAD framework", page_icon="🛠️", layout="wide")
st.title("🛠️ CAD Framework")


STL_PATH = os.path.normpath(str(STL_OUTPUT))
IMAGE_DIR = os.path.normpath(str(OUTPUT_FOLDER))

# Initialize Session States
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_bucket" not in st.session_state:
    st.session_state.current_bucket = ""
if "last_generated_code" not in st.session_state:
    st.session_state.last_generated_code = ""

# --- HELPER: DB FETCH ---
async def fetch_db_requirements(thread_id):
    try:
        async with AsyncConnectionPool(conninfo=DB_URI, min_size=1, max_size=2) as pool:
            cp = AsyncPostgresSaver(pool)
            await cp.setup()
            graph = create_cad_graph(cp)
            state = await graph.aget_state({"configurable": {"thread_id": thread_id}})
            return state.values.get("active_requirements", "")
    except: return ""

# --- SIDEBAR (3D Viewer, Specs, Code & Images) ---
with st.sidebar:
    st.header("Control Center")
    project_id = st.text_input("Project (Thread ID)")
    
    if st.button("Clear Visual Chat"):
        st.session_state.messages = []
        st.session_state.current_bucket = ""
        st.session_state.last_generated_code = ""
        st.rerun()
    
    st.divider()
    st.subheader("📦 Integrated 3D Model")
    
    if os.path.exists(STL_PATH) and os.path.getsize(STL_PATH) > 0:
        try:
            with open(STL_PATH, "rb") as f:
                raw_bytes = f.read()
                stl_data = base64.b64encode(raw_bytes).decode()
            
            st.download_button("💾 Download STL", data=raw_bytes, file_name=f"{project_id}.stl", width='stretch')

            st.components.v1.html(f"""
                <div id="v" style="width:100%; height:320px; background: radial-gradient(#2c3e50, #000000); border-radius:15px;"></div>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
                <script src="https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/js/loaders/STLLoader.js"></script>
                <script src="https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/js/controls/OrbitControls.js"></script>
                <script>
                    const container = document.getElementById('v');
                    const w = container.clientWidth; const h = 320;
                    const s = new THREE.Scene();
                    const c = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
                    const r = new THREE.WebGLRenderer({{antialias:true, alpha:true}});
                    r.setSize(w, h); container.appendChild(r.domElement);
                    s.add(new THREE.DirectionalLight(0xffffff, 1.2)); s.add(new THREE.AmbientLight(0xffffff, 0.4));
                    const loader = new THREE.STLLoader();
                    const geometry = loader.parse(Uint8Array.from(atob("{stl_data}"), x=>x.charCodeAt(0)).buffer);
                    const mesh = new THREE.Mesh(geometry, new THREE.MeshPhongMaterial({{color:0xff9900, specular:0x333333, shininess:100}}));
                    geometry.computeBoundingBox();
                    const ctr = new THREE.Vector3(); geometry.boundingBox.getCenter(ctr);
                    mesh.position.sub(ctr); s.add(mesh);
                    const size = geometry.boundingBox.getSize(new THREE.Vector3()).length();
                    c.position.set(size*1.8, size*1.8, size*1.8); c.lookAt(0,0,0);
                    new THREE.OrbitControls(c, r.domElement);
                    function anim(){{ requestAnimationFrame(anim); r.render(s, c); }}
                    anim();
                </script>
            """, height=340)
        except Exception as e:
            st.error(f"Viewer Error: {e}")
    else:
        st.info("No model found yet.")

    # --- CODE VIEWER ---
    with st.expander("📝 View Generated Code"):
        if st.session_state.last_generated_code:
            st.code(st.session_state.last_generated_code, language='python')
        else:
            st.caption("No code generated in this thread yet.")

    st.divider()
    st.subheader("📋 Requirements Bucket")
    if not st.session_state.current_bucket:
        st.session_state.current_bucket = asyncio.run(fetch_db_requirements(project_id))
    
    if st.session_state.current_bucket:
        reqs = [r.strip("- ") for r in st.session_state.current_bucket.split('\n') if r.strip()]
        for r in reqs:
            if "FIX:" in r: st.error(f"🔧 {r}")
            elif "UPDATE:" in r: st.warning(f"📝 {r}")
            else: st.success(f"✅ {r}")

    st.divider()
    st.subheader("📸 Inspector Visual QA")
    views = ["view_iso.png", "view_front.png", "view_top.png", "view_right.png"]
    cols = st.columns(2)
    for idx, v in enumerate(views):
        p = os.path.join(IMAGE_DIR, v)
        if os.path.exists(p):
            cols[idx % 2].image(p, width='stretch', caption=v.replace('view_', '').replace('.png', '').capitalize())

# --- CHAT & LOGIC (COLLAPSIBLE HISTORY) ---
for i, message in enumerate(st.session_state.messages):
    role = message["role"]
    content = message["content"]
    
    with st.chat_message(role):
        if role == "assistant":
            title = content.split('\n')[0].replace('*', '') if '\n' in content else "System Details"
            is_latest = (i == len(st.session_state.messages) - 1)
            with st.expander(f"👁️ {title}", expanded=is_latest):
                st.markdown(content)
        else:
            st.markdown(content)

async def run_cad_logic(user_input):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    async with AsyncConnectionPool(conninfo=DB_URI, min_size=1, max_size=5, timeout=120) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        graph = create_cad_graph(checkpointer)
        config = {"configurable": {"thread_id": project_id}}
        
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.markdown(user_input)

        with st.chat_message("assistant"):
            ph = st.empty()
            full_resp = ""
            state = await graph.aget_state(config)
            
            processed_input = user_input
            if state.next and not any(x in user_input.lower() for x in ["confirm", "inspector", "feedback:"]):
                 processed_input = f"refine: {user_input}"

            if state.next:
                stream = graph.astream(Command(resume=processed_input), config, stream_mode="updates")
            else:
                stream = graph.astream({"messages": [("user", user_input)]}, config, stream_mode="updates")

            async for event in stream:
                for node, output in event.items():
                    if "active_requirements" in output:
                        st.session_state.current_bucket = output["active_requirements"]
                    
                    # FIXED: We now listen to the 'coder' node and use the 'current_code' key
                    if node == "coder" and "current_code" in output:
                        st.session_state.last_generated_code = output["current_code"]

                    if node == "inspector" and "metadata" in output:
                        full_resp += f"**Inspector:**\n{output['metadata'].get('inspector_critique', '')}\n\n"
                    elif 'messages' in output:
                        m = output['messages'][-1]
                        txt = m[1] if isinstance(m, tuple) else (m.content if hasattr(m, 'content') else str(m))
                        if node == "architect": full_resp += f"**Architect:**\n{txt}\n\n"
                        elif node == "executor": full_resp += f"🚀 **System:** Render Complete.\n\n"
                    ph.markdown(full_resp)
            
            st.session_state.messages.append({"role": "assistant", "content": full_resp})
            st.rerun()

# --- THE UI GATE ( Trinity of Control ) ---
async def get_current_state():
    try:
        async with AsyncConnectionPool(conninfo=DB_URI, min_size=1, max_size=2) as pool:
            cp = AsyncPostgresSaver(pool)
            await cp.setup()
            graph = create_cad_graph(cp)
            return await graph.aget_state({"configurable": {"thread_id": project_id}})
    except: return None

curr = asyncio.run(get_current_state())

if curr and curr.next:
    st.write("---")
    st.markdown("##### ⚡ Direct Actions")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🚀 Confirm & Build Model", width='stretch', type="primary"):
            asyncio.run(run_cad_logic("confirm"))
    with c2:
        if st.button("🔍 Run Inspector Audit", width='stretch'):
            asyncio.run(run_cad_logic("inspector"))
    with c3:
        with st.popover("💻 Send Feedback to the coder agent", width='stretch'):
            f_text = st.text_input("Tell the Coder what to fix:")
            if st.button("Submit Feedback"):
                if f_text: asyncio.run(run_cad_logic(f"feedback: {f_text}"))

if prompt := st.chat_input("Chat with the Architect to build or refine your plan..."):
    asyncio.run(run_cad_logic(prompt))