import test from 'node:test';
import assert from 'node:assert/strict';
import {handle,Env} from '../src/index';
const env:Env={SUPABASE_URL:'https://project.supabase.co',SUPABASE_PUBLISHABLE_KEY:'public-test-key',ALLOWED_ORIGIN:'http://localhost:5173'};
const user='00000000-0000-4000-8000-000000000001';
const target='00000000-0000-4000-8000-000000000002';
const run='00000000-0000-4000-8000-000000000003';
const token='Bearer test-token';
function request(path:string,method='GET',data?:unknown){return new Request('https://api.example'+path,{method,headers:{authorization:token,'content-type':'application/json'},body:data===undefined?undefined:JSON.stringify(data)})}
const mock=(handler?:(url:string,init?:RequestInit)=>Response)=>(async(input:RequestInfo|URL,init?:RequestInit)=>{
 const url=String(input);if(url.endsWith('/auth/v1/user'))return Response.json({id:user});return handler?handler(url,init):Response.json([]);
}) as typeof fetch;
test('health accurately states metadata-only mode',async()=>{const r=await handle(new Request('https://api.example/api/health'),env);assert.equal(r.status,200);assert.equal((await r.json()).inference,false)});
test('unauthenticated request is denied before network access',async()=>{let calls=0;const r=await handle(new Request('https://api.example/api/targets'),env,mock(()=>{calls++;return Response.json([])}));assert.equal(r.status,401);assert.equal(calls,0)});
test('invalid authenticated identity denied',async()=>{const r=await handle(request('/api/targets'),env,(async()=>Response.json({id:'attacker'})) as typeof fetch);assert.equal(r.status,401)});
test('expired token denied',async()=>{const r=await handle(request('/api/targets'),env,(async()=>new Response('',{status:401})) as typeof fetch);assert.equal(r.status,401)});
test('malicious origin denied',async()=>{const r=await handle(new Request('https://api.example/api/targets',{headers:{origin:'https://evil.example',authorization:token}}),env);assert.equal(r.status,403);assert.equal(r.headers.get('access-control-allow-origin'),null)});
test('secret target fields rejected',async()=>{const r=await handle(request('/api/targets','POST',{name:'x',kind:'model',provider:'openai',api_key:'secret'}),env,mock());assert.equal(r.status,400)});
test('arbitrary endpoints stored but never fetched',async()=>{const urls:string[]=[];const r=await handle(request('/api/targets','POST',{name:'local',kind:'model',provider:'ollama',endpoint:'http://127.0.0.1:11434'}),env,mock((url,init)=>{urls.push(url);const data=JSON.parse(String(init?.body));assert.equal(data.user_id,user);assert.equal(init?.headers&&(init.headers as Record<string,string>).authorization,token);return Response.json([data])}));assert.equal(r.status,201);assert.equal(urls.length,1);assert.ok(urls[0].startsWith(env.SUPABASE_URL+'/rest/v1/'))});
test('client cannot promote evidence to verified',async()=>{const r=await handle(request('/api/evidence','POST',{run_id:run,manifest_sha256:'a'.repeat(64),runner_version:'1',tasks:[],trust:'verified'}),env,mock());assert.equal(r.status,400)});
test('foreign target cannot create a run',async()=>{const r=await handle(request('/api/runs','POST',{target_id:target,suite_slug:'structured-agent',suite_version:'1.0',idempotency_key:run}),env,mock());assert.equal(r.status,404)});
test('oversize payload rejected',async()=>{const r=await handle(request('/api/targets','POST',{name:'x'.repeat(1024*1024+1)}),env,mock());assert.equal(r.status,413)});
test('duplicate evidence returns conflict',async()=>{const r=await handle(request('/api/evidence','POST',{run_id:run,manifest_sha256:'a'.repeat(64),runner_version:'1',tasks:[]}),env,mock((url)=>url.includes('run_requests?')?Response.json([{id:run}]):new Response('',{status:409})));assert.equal(r.status,409)});
test('security headers accompany failures',async()=>{const r=await handle(request('/unknown'),env,mock());assert.equal(r.status,404);assert.equal(r.headers.get('x-content-type-options'),'nosniff');assert.ok(r.headers.get('x-request-id'));assert.equal(r.headers.get('cache-control'),'no-store')});

test('malformed endpoint returns validation error',async()=>{const r=await handle(request('/api/targets','POST',{name:'x',kind:'model',provider:'openai',endpoint:'broken'}),env,mock());assert.equal(r.status,400)});
test('credential-bearing endpoints rejected',async()=>{for(const endpoint of ['https://user:password@example.com','https://example.com?key=secret','file:///etc/passwd']){const r=await handle(request('/api/targets','POST',{name:'x',kind:'model',provider:'openai',endpoint}),env,mock());assert.equal(r.status,400)}});
