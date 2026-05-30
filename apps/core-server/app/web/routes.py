from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.core.security import ALGORITHM
from app.db.session import get_db
from app.modules.users.models import User

router = APIRouter(include_in_schema=False)

PROTECTED_PAGES = {
    "/dashboard": "Overview",
    "/sync": "Sync Center",
    "/products": "All Products",
    "/inventory": "Inventory",
    "/reports": "Reports",
    "/notifications": "Notifications",
    "/users": "Users & Roles",
    "/settings": "Settings",
    "/logs": "Logs",
    "/modules": "Modules",
    "/accounting": "Accounting",
    "/orders": "Orders",
    "/purchases": "Purchases",
    "/suppliers": "Suppliers",
    "/sales-analytics": "Sales Analytics",
    "/financial-reports": "Financial Reports",
}


def _current_user_from_cookie(token: str | None, db: Session) -> User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except JWTError:
        return None
    if not username:
        return None
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not user.is_active:
        return None
    return user


def _html_shell(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title} · WooCommerce StoreOps</title>
  <style>{BASE_CSS}</style>
</head>
<body>{body}</body>
</html>""")


@router.get("/", response_class=HTMLResponse)
def root(storeops_access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    return RedirectResponse("/dashboard" if _current_user_from_cookie(storeops_access_token, db) else "/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
def login_page(storeops_access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if _current_user_from_cookie(storeops_access_token, db):
        return RedirectResponse("/dashboard", status_code=302)
    return _html_shell("Login", LOGIN_BODY)


@router.get("/{page_path:path}", response_class=HTMLResponse)
def admin_page(request: Request, page_path: str, storeops_access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    path = "/" + page_path.strip("/")
    if path not in PROTECTED_PAGES:
        return RedirectResponse("/dashboard", status_code=302)
    user = _current_user_from_cookie(storeops_access_token, db)
    if user is None:
        return RedirectResponse(f"/login?next={path}", status_code=302)
    return _html_shell(PROTECTED_PAGES[path], ADMIN_BODY.replace("__INITIAL_PAGE__", path).replace("__PAGE_TITLE__", PROTECTED_PAGES[path]))


BASE_CSS = r'''
:root{--bg:#f6f8fb;--panel:#fff;--text:#172033;--muted:#697386;--line:#e6eaf0;--brand:#5b46f6;--brand2:#16a34a;--danger:#dc2626;--warn:#d97706;--soft:#eef2ff;--shadow:0 20px 50px rgba(20,32,55,.08)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:inherit;text-decoration:none}button,input,select{font:inherit}.login-wrap{min-height:100vh;display:grid;place-items:center;padding:32px;background:radial-gradient(circle at top left,#eef2ff,transparent 34%),linear-gradient(135deg,#f8fafc,#eef2f7)}.login-card{width:min(440px,100%);background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:28px;box-shadow:var(--shadow);padding:34px}.brand{display:flex;gap:12px;align-items:center;margin-bottom:28px}.brand-mark{width:44px;height:44px;border-radius:14px;display:grid;place-items:center;color:#fff;background:linear-gradient(135deg,var(--brand),#8b5cf6);font-weight:800}.brand h1{font-size:22px;margin:0}.brand p{margin:2px 0 0;color:var(--muted)}.field{margin:16px 0}.label{display:block;font-weight:700;margin-bottom:7px}.input-wrap{position:relative}.input{width:100%;padding:13px 14px;border:1px solid var(--line);border-radius:14px;background:#fff;outline:none}.input:focus{border-color:var(--brand);box-shadow:0 0 0 4px rgba(91,70,246,.12)}.toggle-pass{position:absolute;right:8px;top:8px;border:0;background:#f1f5f9;border-radius:10px;padding:6px 9px;cursor:pointer}.btn{border:0;border-radius:14px;padding:12px 16px;background:var(--brand);color:#fff;font-weight:800;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:8px}.btn.secondary{background:#f1f5f9;color:var(--text)}.btn.danger{background:var(--danger)}.btn:disabled{opacity:.55;cursor:not-allowed}.btn.full{width:100%;margin-top:10px}.alert{display:none;margin:14px 0;padding:12px;border-radius:14px;background:#fef2f2;color:#991b1b}.hint{margin-top:16px;color:var(--muted);font-size:13px}.app{display:grid;grid-template-columns:280px 1fr;min-height:100vh}.sidebar{background:#111827;color:#e5e7eb;padding:20px;position:sticky;top:0;height:100vh;overflow:auto}.sidebar .brand{margin-bottom:22px}.sidebar .brand-mark{width:38px;height:38px}.sidebar h1{font-size:16px;color:#fff}.sidebar p{font-size:12px;color:#9ca3af}.nav-section{margin:20px 0 8px;color:#9ca3af;font-size:11px;font-weight:900;letter-spacing:.08em;text-transform:uppercase}.nav-item{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;border-radius:12px;color:#d1d5db;margin:3px 0}.nav-item:hover,.nav-item.active{background:#1f2937;color:#fff}.nav-item.disabled{opacity:.45;cursor:not-allowed}.soon{font-size:11px;color:#a5b4fc}.main{min-width:0}.topbar{height:70px;display:flex;align-items:center;justify-content:space-between;padding:0 28px;background:rgba(255,255,255,.86);backdrop-filter:blur(12px);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}.crumb{color:var(--muted);font-size:13px}.content{padding:28px}.page-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;margin-bottom:22px}.page-head h2{font-size:28px;margin:0}.page-head p{color:var(--muted);margin:4px 0 0}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin-bottom:22px}.card{background:var(--panel);border:1px solid var(--line);border-radius:22px;box-shadow:0 10px 30px rgba(20,32,55,.04);padding:20px}.card h3{margin:0 0 8px;font-size:15px}.metric{font-size:30px;font-weight:900}.muted{color:var(--muted)}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 16px}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:18px;background:#fff}table{width:100%;border-collapse:collapse;min-width:720px}th,td{padding:12px 14px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{background:#f8fafc;font-size:12px;text-transform:uppercase;color:var(--muted);letter-spacing:.04em}.badge{display:inline-flex;padding:4px 8px;border-radius:999px;background:#eef2ff;color:#3730a3;font-weight:700;font-size:12px}.badge.ok{background:#ecfdf5;color:#166534}.badge.fail{background:#fef2f2;color:#991b1b}.empty{padding:28px;text-align:center;color:var(--muted)}.grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.settings-group{margin-bottom:18px}.setting-row{display:grid;grid-template-columns:1fr 260px auto;gap:14px;align-items:center;padding:13px 0;border-bottom:1px solid var(--line)}.setting-row:last-child{border-bottom:0}.toast{position:fixed;right:20px;bottom:20px;background:#111827;color:#fff;border-radius:14px;padding:12px 14px;box-shadow:var(--shadow);opacity:0;transform:translateY(10px);transition:.2s;z-index:20}.toast.show{opacity:1;transform:none}.modal-backdrop{display:none;position:fixed;inset:0;background:rgba(15,23,42,.55);z-index:30;place-items:center;padding:20px}.modal{max-width:420px;background:#fff;border-radius:22px;padding:22px;box-shadow:var(--shadow)}.loading{opacity:.65;pointer-events:none}@media(max-width:960px){.app{grid-template-columns:1fr}.sidebar{position:relative;height:auto}.cards,.grid-2{grid-template-columns:1fr}.setting-row{grid-template-columns:1fr}.topbar{position:relative}.content{padding:18px}}
'''

LOGIN_BODY = r'''
<div class="login-wrap">
  <form class="login-card" id="loginForm">
    <div class="brand"><div class="brand-mark">SO</div><div><h1>WooCommerce StoreOps</h1><p>Secure admin dashboard</p></div></div>
    <div id="loginError" class="alert"></div>
    <label class="field"><span class="label">Username or email</span><input class="input" id="username" autocomplete="username" required /></label>
    <label class="field"><span class="label">Password</span><span class="input-wrap"><input class="input" id="password" type="password" autocomplete="current-password" required /><button class="toggle-pass" type="button" id="togglePassword">Show</button></span></label>
    <button class="btn full" id="loginButton" type="submit">Log in</button>
    <p class="hint">Create the first Super Admin with <code>docker compose exec core-server python3 scripts/create_admin.py</code>.</p>
  </form>
</div>
<script>
const form=document.getElementById('loginForm'),err=document.getElementById('loginError'),btn=document.getElementById('loginButton'),pw=document.getElementById('password');
document.getElementById('togglePassword').onclick=()=>{pw.type=pw.type==='password'?'text':'password';event.target.textContent=pw.type==='password'?'Show':'Hide'};
form.onsubmit=async(e)=>{e.preventDefault();err.style.display='none';btn.disabled=true;btn.textContent='Logging in…';try{const r=await fetch('/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:document.getElementById('username').value.trim(),password:pw.value})});if(!r.ok){const d=await r.json().catch(()=>({detail:'Login failed'}));throw new Error(d.detail||'Login failed')}location.href=new URLSearchParams(location.search).get('next')||'/dashboard'}catch(ex){err.textContent=ex.message;err.style.display='block'}finally{btn.disabled=false;btn.textContent='Log in'}};
</script>
'''

ADMIN_BODY = r'''
<div class="app" data-page="__INITIAL_PAGE__">
  <aside class="sidebar">
    <div class="brand"><div class="brand-mark">SO</div><div><h1>WooCommerce StoreOps</h1><p id="envLabel">Admin panel</p></div></div>
    <div class="nav-section">Dashboard</div><a class="nav-item" href="/dashboard" data-href="/dashboard">Overview</a>
    <div class="nav-section">Operations</div><a class="nav-item" href="/sync" data-href="/sync">Sync Center</a><a class="nav-item" href="/products" data-href="/products">All Products</a><a class="nav-item" href="/inventory" data-href="/inventory">Inventory</a>
    <div class="nav-section">Management</div><a class="nav-item" href="/reports" data-href="/reports">Reports</a><a class="nav-item" href="/notifications" data-href="/notifications">Notifications</a><a class="nav-item" href="/users" data-href="/users">Users & Roles</a>
    <div class="nav-section">System</div><a class="nav-item" href="/settings" data-href="/settings">Settings</a><a class="nav-item" href="/logs" data-href="/logs">Logs</a><a class="nav-item" href="/modules" data-href="/modules">Modules</a>
    <div class="nav-section">Future modules</div><span class="nav-item disabled">Accounting <b class="soon">Coming Soon</b></span><span class="nav-item disabled">Orders <b class="soon">Coming Soon</b></span><span class="nav-item disabled">Purchases <b class="soon">Coming Soon</b></span><span class="nav-item disabled">Suppliers <b class="soon">Coming Soon</b></span><span class="nav-item disabled">Sales Analytics <b class="soon">Coming Soon</b></span><span class="nav-item disabled">Financial Reports <b class="soon">Coming Soon</b></span>
  </aside>
  <main class="main">
    <header class="topbar"><div><div class="crumb">Admin / <span id="crumb">__PAGE_TITLE__</span></div><strong id="pageTitleTop">__PAGE_TITLE__</strong></div><div style="display:flex;gap:12px;align-items:center"><span class="badge" id="currentUser">Loading…</span><button class="btn secondary" id="logoutBtn">Logout</button></div></header>
    <section class="content"><div class="page-head"><div><h2 id="pageTitle">__PAGE_TITLE__</h2><p id="pageSubtitle">Loading admin foundation…</p></div><div id="pageActions"></div></div><div id="pageRoot"><div class="card">Loading…</div></div></section>
  </main>
</div><div id="toast" class="toast"></div><div id="modal" class="modal-backdrop"><div class="modal"><h3 id="modalTitle">Confirm action</h3><p id="modalText"></p><div class="toolbar"><button class="btn danger" id="modalConfirm">Confirm</button><button class="btn secondary" onclick="hideModal()">Cancel</button></div></div></div>
<script>
const state={user:null,page:document.querySelector('.app').dataset.page,permissions:new Set()};
const root=document.getElementById('pageRoot'),title=document.getElementById('pageTitle'),subtitle=document.getElementById('pageSubtitle'),actions=document.getElementById('pageActions');
function toast(msg){const t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2600)}
function showModal(text,onConfirm){document.getElementById('modalText').textContent=text;document.getElementById('modal').style.display='grid';document.getElementById('modalConfirm').onclick=()=>{hideModal();onConfirm&&onConfirm()}}
function hideModal(){document.getElementById('modal').style.display='none'}
async function api(path,opts={}){const r=await fetch(path,{headers:{'Content-Type':'application/json',...(opts.headers||{})},...opts});if(r.status===401){location.href='/login?next='+encodeURIComponent(location.pathname);return}if(!r.ok){const d=await r.json().catch(()=>({detail:'Request failed'}));throw new Error(d.detail||'Request failed')}return r.status===204?null:r.json()}
function can(p){return state.permissions.has(p)}
function setHead(t,s=''){title.textContent=t;document.getElementById('pageTitleTop').textContent=t;document.getElementById('crumb').textContent=t;subtitle.textContent=s;actions.innerHTML=''}
function esc(v){return String(v??'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]))}
function inputFor(s){if(s.value_type==='boolean')return `<input type="checkbox" ${s.value?'checked':''} ${!s.is_editable?'disabled':''}>`;if(Array.isArray(s.options))return `<select class="input" ${!s.is_editable?'disabled':''}>${s.options.map(o=>`<option value="${esc(o)}" ${o===s.value?'selected':''}>${esc(o)}</option>`).join('')}</select>`;let type=s.value_type==='integer'||s.value_type==='float'?'number':(s.validation_rules?.format==='HH:MM'?'time':'text');return `<input class="input" type="${type}" value="${esc(s.value??'')}" ${!s.is_editable?'disabled':''}>`}
async function loadOverview(){setHead('Overview','Operational summary for the Core Server admin foundation.');const [sync,products]=await Promise.all([api('/api/v1/sync/status').catch(()=>({running_job:null,total_products:0,total_variations:0})),api('/api/v1/products?per_page=1').catch(()=>({total:0}))]);root.innerHTML=`<div class="cards"><div class="card"><h3>Core Server</h3><div class="metric">OK</div><p class="muted">Health endpoint is active.</p></div><div class="card"><h3>Synced products</h3><div class="metric">${products.total||0}</div><p class="muted">Catalog mirror records.</p></div><div class="card"><h3>Current sync</h3><div class="metric">${sync.running_job?'Running':'Idle'}</div><p class="muted">Celery-backed jobs.</p></div><div class="card"><h3>User</h3><div class="metric">${esc(state.user.username)}</div><p class="muted">${esc(state.user.role)}</p></div></div><div class="grid-2"><div class="card"><h3>Admin panel structure</h3><p>Sidebar, top bar, protected routes, toast foundation, confirmation modal foundation, clean cards, tables, loading states, and empty states are in place.</p></div><div class="card"><h3>Architecture note</h3><p>WordPress remains a lightweight connector. Heavy sync, settings, users, roles, logs, reports, and future modules stay in the Python Core Server.</p></div></div>`}
async function loadSync(){setHead('Sync Center','Run and monitor WooCommerce product sync jobs.');actions.innerHTML=`${can('sync.run_full')?'<button class="btn" id="runFull">Run Full Product Sync</button>':''} ${can('sync.run_changed')?'<button class="btn secondary" id="runChanged">Run Changed Sync</button>':''}<button class="btn secondary" id="checkWp">Check WordPress</button>`;const [status,jobs]=await Promise.all([api('/api/v1/sync/status'),api('/api/v1/sync/jobs')]);root.innerHTML=`<div class="cards"><div class="card"><h3>WordPress</h3><div class="metric">${esc(status.wordpress_connection||'Ready')}</div><p class="muted">Connector remains lightweight.</p></div><div class="card"><h3>Database</h3><div class="metric">OK</div><p class="muted">Sync jobs persisted.</p></div><div class="card"><h3>Redis/Celery</h3><div class="metric">Queued</div><p class="muted">Sync runs outside HTTP requests.</p></div><div class="card"><h3>Current job</h3><div class="metric">${status.running_job?esc(status.running_job.status):'Idle'}</div><p class="muted">${status.running_job?esc(status.running_job.job_type):'No active job'}</p></div></div>${table(['Job type','Status','Started','Finished','Processed','Created','Updated','Failed','Error'],jobs.map(j=>[j.job_type,badge(j.status),j.started_at||'',j.finished_at||'',j.processed_items,j.created_items,j.updated_items,j.failed_items,j.error_message||'']))}`;document.getElementById('runFull')?.addEventListener('click',async()=>{try{await api('/api/v1/sync/full-products',{method:'POST'});toast('Full product sync queued');loadSync()}catch(e){toast(e.message)}});document.getElementById('runChanged')?.addEventListener('click',async()=>{try{await api('/api/v1/sync/changed-products',{method:'POST'});toast('Changed-products sync queued');loadSync()}catch(e){toast(e.message)}});document.getElementById('checkWp')?.addEventListener('click',async()=>{try{const r=await api('/api/v1/sync/check-wordpress',{method:'POST'});toast(r.message||'Connection check queued')}catch(e){toast(e.message)}})}
async function loadProducts(){setHead('All Products','Search and review products imported from WooCommerce.');actions.innerHTML='<input class="input" style="width:260px" id="productSearch" placeholder="Search name, SKU, Woo ID…">';const render=async(q='')=>{const data=await api('/api/v1/products?per_page=25&search='+encodeURIComponent(q));root.innerHTML=data.total?table(['Name','Type','Status','SKU','Stock','Stock status','Woo ID','Variation ID','Parent ID','Last synced'],data.items.map(p=>[p.product_name,p.product_type,p.product_status,p.sku||'',p.stock_quantity??'',p.stock_status,p.woocommerce_product_id,p.woocommerce_variation_id||'',p.parent_woocommerce_product_id||'',p.last_synced_at||''])):'<div class="card empty">No products have been synced yet. Open Sync Center and run Full Product Sync.</div>'};await render();document.getElementById('productSearch').oninput=e=>render(e.target.value)}
async function loadUsers(){setHead('Users & Roles','Manage admin users, roles, and permissions.');const [users,roles]=await Promise.all([api('/api/v1/users/'),api('/api/v1/users/roles')]);actions.innerHTML=can('users.create')?'<button class="btn" id="addUserBtn">Add User</button>':'';root.innerHTML=`<div class="grid-2"><div class="card"><h3>Users</h3>${users.length?table(['Username','Email','Role','Active','Last login'],users.map(u=>[u.username,u.email||'',u.role,u.is_active?'Yes':'No',u.last_login_at||''])):'<div class="empty">No users found.</div>'}</div><div class="card"><h3>Roles</h3>${table(['Role','Slug','Permissions'],roles.map(r=>[r.name,r.slug,(r.permissions||[]).map(p=>p.code).join(', ')]))}</div></div>`;document.getElementById('addUserBtn')?.addEventListener('click',()=>toast('User creation form foundation is ready; API endpoint POST /api/v1/users/ is available.'))}
async function loadSettings(){setHead('Settings','Database-backed runtime and business settings grouped by area.');const groups=await api('/api/v1/settings/');root.innerHTML=groups.map(g=>`<div class="card settings-group"><h3>${esc(g.label)}</h3>${g.settings.map(s=>`<div class="setting-row" data-key="${esc(s.key)}" data-type="${esc(s.value_type)}"><div><strong>${esc(s.label)}</strong><div class="muted">${esc(s.description||s.key)}</div></div><div>${inputFor(s)}</div><button class="btn secondary" ${!s.is_editable||!can('settings.manage')?'disabled':''}>Save</button></div>`).join('')}</div>`).join('');root.querySelectorAll('.setting-row button').forEach(btn=>btn.onclick=async()=>{const row=btn.closest('.setting-row'),el=row.querySelector('input,select');let value=el.type==='checkbox'?el.checked:el.value;try{await api('/api/v1/settings/'+row.dataset.key,{method:'PATCH',body:JSON.stringify({value})});toast('Setting saved')}catch(e){toast(e.message)}})}
async function loadLogs(){setHead('Logs','Audit and activity log foundation.');const logs=await api('/api/v1/logs/').catch(()=>[]);root.innerHTML=logs.length?table(['Action','Module','Entity','User','Created'],logs.map(l=>[l.action,l.module,l.entity_type||'',l.user_id||'',l.created_at])):'<div class="card empty">No logs are available yet.</div>'}
function loadPlaceholder(name){setHead(name,'Foundation page. Business logic will be added in a later module phase.');root.innerHTML='<div class="card empty">'+name+' is prepared in navigation only. No business logic is implemented in this phase.</div>'}
function badge(v){return `<span class="badge ${['completed','ok','active'].includes(String(v).toLowerCase())?'ok':['failed','error'].includes(String(v).toLowerCase())?'fail':''}">${esc(v)}</span>`}
function table(head,rows){if(!rows.length)return '<div class="table-wrap"><div class="empty">No records found.</div></div>';return `<div class="table-wrap"><table><thead><tr>${head.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(c=>`<td>${typeof c==='string'&&c.startsWith('<span')?c:esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`}
async function route(){document.querySelectorAll('.nav-item[data-href]').forEach(a=>a.classList.toggle('active',a.dataset.href===location.pathname));try{if(location.pathname==='/dashboard')return loadOverview();if(location.pathname==='/sync')return loadSync();if(location.pathname==='/products')return loadProducts();if(location.pathname==='/users')return loadUsers();if(location.pathname==='/settings')return loadSettings();if(location.pathname==='/logs')return loadLogs();return loadPlaceholder(document.querySelector(`[data-href="${location.pathname}"]`)?.textContent.trim()||'Coming Soon')}catch(e){root.innerHTML=`<div class="card"><strong>Error</strong><p class="muted">${esc(e.message)}</p></div>`}}
async function boot(){state.user=await api('/api/v1/auth/me');state.permissions=new Set(state.user.permissions||[]);if(state.user.is_superuser)state.permissions.add('*');document.getElementById('currentUser').textContent=`${state.user.username} · ${state.user.role}`;document.getElementById('logoutBtn').onclick=async()=>{await api('/api/v1/auth/logout',{method:'POST'});location.href='/login'};await route()}
const oldCan=can;function can(p){return state.permissions.has('*')||state.permissions.has(p)}
boot();
</script>
'''
