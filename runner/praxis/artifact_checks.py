"""Local artifact inspection. Unknown executable workloads are rejected by default."""
import hashlib
import json
import mimetypes
import struct
from pathlib import Path

MAX_BYTES=20*1024*1024

def inspect_artifact(path):
    path=Path(path)
    size=path.stat().st_size
    if size>MAX_BYTES:
        raise ValueError("Artifact exceeds 20 MiB")
    data=path.read_bytes()
    mime=mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    metadata={"filename":path.name,"size":size,"mime":mime,"sha256":hashlib.sha256(data).hexdigest()}
    if data.startswith(b'\x89PNG\r\n\x1a\n') and len(data)>=24:
        metadata.update(mime="image/png",width=struct.unpack('>I',data[16:20])[0],height=struct.unpack('>I',data[20:24])[0])
    if data.startswith(b'RIFF') and data[8:12]==b'WAVE':
        import wave
        with wave.open(str(path),'rb') as clip:
            metadata.update(mime="audio/wav",duration_seconds=clip.getnframes()/clip.getframerate(),sample_rate=clip.getframerate(),channels=clip.getnchannels())
    return metadata

def execute_untrusted_code(*args,**kwargs):
    raise RuntimeError("Untrusted executable workloads are unsupported without a configured isolated executor; execution denied")

OWNED_WEB_FIXTURE = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Praxis owned shop fixture</title><style>body{font:16px sans-serif;max-width:800px;margin:auto;padding:16px}button,input{font:inherit;padding:8px}article{padding:16px;border:1px solid #888}#items{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px}</style><h1>Fixture stationery</h1><label for="search">Search</label><input id="search"><main id="items"><article data-name="Red book">Red book <button id="add">Add book</button></article><article data-name="Blue pen">Blue pen</article></main><p>Cart quantity: <output id="quantity">0</output></p><form><label for="email">Email</label><input id="email" type="email" required><button>Checkout</button></form><script>document.querySelector('#add').onclick=()=>document.querySelector('#quantity').value=Number(document.querySelector('#quantity').value)+1;document.querySelector('#search').oninput=e=>document.querySelectorAll('article').forEach(x=>x.hidden=!x.dataset.name.toLowerCase().includes(e.target.value.toLowerCase()));document.querySelector('form').onsubmit=e=>e.preventDefault()</script></html>'''

def check_owned_website(output_dir, html=None):
    """Only the source-controlled harness fixture is allowed outside an OS sandbox.

    Browser context blocks all outbound requests, has no inherited storage and is
    never the application origin. This is a fixture test, not arbitrary HTML isolation.
    """
    if html is not None and html!=OWNED_WEB_FIXTURE:
        raise RuntimeError("Untrusted HTML execution denied: configure an isolated executor")
    from playwright.sync_api import sync_playwright
    folder=Path(output_dir)
    folder.mkdir(parents=True,exist_ok=True)
    checks=[]
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(viewport={"width":1280,"height":800},service_workers="block")
        context.route("**/*",lambda route:route.abort())
        page=context.new_page()
        page.on("pageerror",lambda error:errors.append(str(error)))
        page.set_content(OWNED_WEB_FIXTURE)
        page.get_by_role("button",name="Add book").click()
        checks.append({"name":"cart interaction","passed":page.locator('#quantity').input_value()=="1","expected":"1","actual":page.locator('#quantity').input_value()})
        page.get_by_label("Search").fill("red")
        checks.append({"name":"search filters items","passed":page.locator('article:visible').count()==1,"expected":1,"actual":page.locator('article:visible').count()})
        page.get_by_label("Email").fill("invalid")
        valid=page.locator('#email').evaluate('(e)=>e.checkValidity()')
        checks.append({"name":"invalid email rejected","passed":not valid,"expected":False,"actual":valid})
        labels=page.locator('input').evaluate_all('(inputs)=>inputs.every(x=>x.labels.length>0)')
        checks.append({"name":"inputs have labels","passed":labels,"expected":True,"actual":labels})
        for width in (390,1280):
            page.set_viewport_size({"width":width,"height":800})
            overflow=page.evaluate('document.documentElement.scrollWidth > innerWidth')
            checks.append({"name":"viewport %s no overflow"%width,"passed":not overflow,"expected":False,"actual":overflow})
            page.screenshot(path=str(folder/('website-%s.png'%width)),full_page=True)
        checks.append({"name":"no runtime errors","passed":not errors,"expected":[],"actual":errors})
        context.close()
        browser.close()
    (folder/'website.html').write_text(OWNED_WEB_FIXTURE)
    result={"trust":"demo","fixture":"owned source-controlled application, not generated model output","assertions":checks,"passed":all(c["passed"] for c in checks),"screenshots":[inspect_artifact(folder/('website-%s.png'%w)) for w in (390,1280)]}
    (folder/'website-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
