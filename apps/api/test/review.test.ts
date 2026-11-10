// @vitest-environment node
import {afterEach,expect,it,vi} from 'vitest';
import worker,{handle,type Env} from '../src/index';
const user='00000000-0000-4000-8000-000000000001',id='00000000-0000-4000-8000-000000000002';
const env:Env={SUPABASE_URL:'https://owned.supabase.co',SUPABASE_PUBLISHABLE_KEY:'public-fixture',ALLOWED_ORIGIN:'https://owned.example'};
function req(path:string,method='GET',data?:unknown,headers:Record<string,string>={}){return new Request('https://metadata.example'+path,{method,headers:{authorization:'Bearer fixture-token','content-type':'application/json',...headers},body:data===undefined?undefined:JSON.stringify(data)})}
function transport(data:unknown=[],status=200){return vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{
 const url=String(input);expect(url.startsWith(env.SUPABASE_URL+'/')).toBe(true);expect(init?.redirect).toBe('error');expect((init?.headers as Record<string,string>).authorization).toBe('Bearer fixture-token');
 return url.endsWith('/auth/v1/user')?Response.json({id:user}):status===204?new Response(null,{status}):Response.json(data,{status});
}) as unknown as typeof fetch;}
afterEach(()=>vi.useRealTimers());
it('health, preflight, exact CORS and unconfigured wrapper',async()=>{
 let r=await handle(req('/api/health'),env);expect(r.status).toBe(200);expect((await r.json()).inference).toBe(false);
 r=await handle(req('/anything','OPTIONS',undefined,{origin:env.ALLOWED_ORIGIN}),env);expect(r.status).toBe(204);expect(r.headers.get('access-control-allow-origin')).toBe(env.ALLOWED_ORIGIN);
 expect((await handle(req('/api/me','GET',undefined,{origin:'https://evil.example'}),env)).status).toBe(403);
 expect((await worker.fetch(req('/api/me'),{...env,SUPABASE_URL:''})).status).toBe(503);
 expect((await handle(req('/api/me'),{...env,SUPABASE_URL:'http://insecure.example'})).status).toBe(503);
});
it('rejects missing/invalid token and invalid/expired identity',async()=>{
 expect((await handle(req('/api/me','GET',undefined,{authorization:''}),env)).status).toBe(401);
 for(const response of [Response.json({id:'forged'}),Response.json({}, {status:401})])expect((await handle(req('/api/me'),env,vi.fn(async()=>response))).status).toBe(401);
 expect((await handle(req('/api/me'),env,vi.fn(async()=>{throw Error('transport detail must not leak')}))).status).toBe(500);
});
it('forwards authenticated identity and has no endpoint proxy',async()=>{
 const fetcher=transport([{id}]);expect((await handle(req('/api/me'),env,fetcher)).status).toBe(200);
 for(const path of ['/api/targets','/api/runs','/api/leaderboards','/api/runs/'+id])expect((await handle(req(path),env,transport([{id}]))).status).toBe(200);
 const r=await handle(req('/api/targets','POST',{name:'owned',kind:'model',provider:'custom',endpoint:'http://127.0.0.1:9000'}),env,fetcher);expect(r.status).toBe(201);
 const calls=vi.mocked(fetcher).mock.calls;expect(calls.every(([url])=>String(url).startsWith(env.SUPABASE_URL))).toBe(true);
 const post=calls.find(([,init])=>init?.method==='POST')!;expect(JSON.parse(String(post[1]?.body)).user_id).toBe(user);
});
it('run and evidence insertion enforce ownership and unverified trust',async()=>{
 for(const [path,data] of [['/api/runs',{target_id:id,suite_slug:'owned',suite_version:'1',idempotency_key:id}],['/api/evidence',{run_id:id,manifest_sha256:'a'.repeat(64),runner_version:'fixture',tasks:[]}] ] as const){
   expect((await handle(req(path,'POST',data),env,transport([{id}]))).status).toBe(201);
   expect((await handle(req(path,'POST',data),env,transport([]))).status).toBe(404);
   expect((await handle(req(path,'POST',{...data,trust:'verified'}),env,transport())).status).toBe(400);
 }
});
it('database failure, duplicate, missing and invalid routes fail safely',async()=>{
 for(const [status,expected] of [[403,403],[409,409],[500,502]])expect((await handle(req('/api/targets'),env,transport({},status))).status).toBe(expected);
 expect((await handle(req('/api/targets'),env,transport(null,204))).status).toBe(200);
 expect((await handle(req('/api/runs/'+id),env,transport([]))).status).toBe(404);
 expect((await handle(req('/api/runs/bad'),env,transport())).status).toBe(400);
 expect((await handle(req('/unknown'),env,transport())).status).toBe(404);
});
it('strict schemas cover endpoint protocols/credentials and request metadata',async()=>{
 for(const endpoint of ['broken','ftp://host','https://name:credential@host','https://host?key=value','https://host#fragment'])expect((await handle(req('/api/targets','POST',{name:'x',kind:'model',provider:'custom',endpoint}),env,transport())).status).toBe(400);
 expect((await handle(req('/api/targets','POST',{name:'ok',kind:'agent',provider:'demo'}),env,transport())).status).toBe(201);
 for(const path of ['/api/targets','/api/runs','/api/evidence'])expect((await handle(req(path,'POST',{}),env,transport())).status).toBe(400);
});
it('body parser rejects media ambiguity, malformed JSON, missing and declared oversize',async()=>{
 const f=transport();
 expect((await handle(req('/api/targets','POST',{}, {'content-type':'application/json-evil'}),env,f)).status).toBe(415);
 expect((await handle(req('/api/targets','POST',{}, {'content-length':'1048577'}),env,f)).status).toBe(413);
 for(const body of [undefined,'invalid',new Uint8Array([255])]){
   const r=new Request('https://metadata.example/api/targets',{method:'POST',headers:{authorization:'Bearer fixture-token','content-type':'application/json'},body});
   expect((await handle(r,env,f)).status).toBe(400);
 }
});
it('streamed byte limit and deadline cancel the body',async()=>{
 let canceled=false;const stream=new ReadableStream({start(c){c.enqueue(new Uint8Array(1048577))},cancel(){canceled=true}});
 const request=new Request('https://metadata.example/api/targets',{method:'POST',headers:{authorization:'Bearer fixture-token','content-type':'application/json'},body:stream,duplex:'half'} as RequestInit);
 expect((await handle(request,env,transport())).status).toBe(413);expect(canceled).toBe(true);
 vi.useFakeTimers();canceled=false;
 const slow=new Request('https://metadata.example/api/targets',{method:'POST',headers:{authorization:'Bearer fixture-token','content-type':'application/json'},body:new ReadableStream({cancel(){canceled=true}}),duplex:'half'} as RequestInit);
 const pending=handle(slow,env,transport());await vi.advanceTimersByTimeAsync(10001);expect((await pending).status).toBe(408);expect(canceled).toBe(true);
});
