import { TargetSchema, RunRequestSchema, EvidenceSchema, MAX_EVIDENCE_BYTES } from '@praxis/contracts';
export interface Env {SUPABASE_URL:string; SUPABASE_PUBLISHABLE_KEY:string; ALLOWED_ORIGIN:string;}
type Fetcher=typeof fetch;
class HttpError extends Error {constructor(public status:number,message:string){super(message)}}
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
function json(data:unknown,status=200){return new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json; charset=utf-8'}})}
async function body(req:Request){
  if(!req.headers.get('content-type')?.startsWith('application/json'))throw new HttpError(415,'Use application/json');
  if(Number(req.headers.get('content-length'))>MAX_EVIDENCE_BYTES)throw new HttpError(413,'Payload limit is 1 MiB');
  const reader=req.body?.getReader();if(!reader)throw new HttpError(400,'JSON body required');
  const chunks:Uint8Array[]=[];let size=0;
  while(true){const next=await reader.read();if(next.done)break;size+=next.value.length;if(size>MAX_EVIDENCE_BYTES){await reader.cancel();throw new HttpError(413,'Payload limit is 1 MiB')}chunks.push(next.value)}
  const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length}
  try{return JSON.parse(new TextDecoder().decode(bytes))}catch{throw new HttpError(400,'Invalid JSON')}
}
export async function handle(req:Request,env:Env,fetcher:Fetcher=fetch):Promise<Response>{
  const requestId=crypto.randomUUID();const origin=req.headers.get('origin');
  let response:Response;
  try{
    if(origin&&origin!==env.ALLOWED_ORIGIN)throw new HttpError(403,'Origin is not allowed');
    if(req.method==='OPTIONS')response=new Response(null,{status:204});
    else if(new URL(req.url).pathname==='/api/health')response=json({service:'praxis',mode:'cloud-metadata',inference:false});
    else{
      if(!env.SUPABASE_URL||!env.SUPABASE_PUBLISHABLE_KEY)throw new HttpError(503,'Supabase is not configured');
      const base=new URL(env.SUPABASE_URL);if(base.protocol!=='https:')throw new HttpError(503,'Supabase URL must use HTTPS');
      const authorization=req.headers.get('authorization');
      if(!authorization?.match(/^Bearer [A-Za-z0-9._-]+$/))throw new HttpError(401,'Bearer access token required');
      const headers={apikey:env.SUPABASE_PUBLISHABLE_KEY,authorization,'content-type':'application/json'};
      const userResponse=await fetcher(new URL('/auth/v1/user',base),{headers,signal:AbortSignal.timeout(10000),redirect:'error'});
      if(!userResponse.ok)throw new HttpError(401,'Access token is invalid or expired');
      const user=await userResponse.json() as {id?:string};if(!user.id||!uuid.test(user.id))throw new HttpError(401,'Invalid authenticated user');
      const db=async(path:string,method='GET',data?:unknown)=>{
        const r=await fetcher(new URL('/rest/v1/'+path,base),{method,headers:{...headers,Prefer:'return=representation'},body:data===undefined?undefined:JSON.stringify(data),signal:AbortSignal.timeout(10000),redirect:'error'});
        if(!r.ok){if(r.status===409)throw new HttpError(409,'Duplicate immutable record or idempotency key');throw new HttpError(r.status===403?403:502,'Database operation failed')}
        return r.status===204?[]:r.json();
      };
      const path=new URL(req.url).pathname;
      if(path==='/api/me'&&req.method==='GET')response=json({user:{id:user.id}});
      else if(path==='/api/targets'&&req.method==='GET')response=json(await db('model_revisions?select=id,name,kind,provider,endpoint,model,capabilities,created_at&order=created_at.desc&limit=100'));
      else if(path==='/api/targets'&&req.method==='POST'){
        const parsed=TargetSchema.safeParse(await body(req));if(!parsed.success)throw new HttpError(400,'Invalid target; credentials and unknown fields are forbidden');
        response=json(await db('model_revisions','POST',{...parsed.data,user_id:user.id}),201);
      }else if(path==='/api/runs'&&req.method==='GET')response=json(await db('run_requests?select=*&order=created_at.desc&limit=100'));
      else if(path==='/api/runs'&&req.method==='POST'){
        const parsed=RunRequestSchema.safeParse(await body(req));if(!parsed.success)throw new HttpError(400,'Invalid versioned run request');
        const targets=await db('model_revisions?id=eq.'+parsed.data.target_id+'&select=id') as unknown[];
        if(targets.length!==1)throw new HttpError(404,'Target not found');
        response=json(await db('run_requests','POST',{...parsed.data,user_id:user.id,status:'queued',trust:'self-reported'}),201);
      }else if(path==='/api/evidence'&&req.method==='POST'){
        const parsed=EvidenceSchema.safeParse(await body(req));if(!parsed.success)throw new HttpError(400,'Invalid evidence; client trust assertions are forbidden');
        const runs=await db('run_requests?id=eq.'+parsed.data.run_id+'&select=id') as unknown[];
        if(runs.length!==1)throw new HttpError(404,'Run not found');
        response=json(await db('run_evidence','POST',{...parsed.data,user_id:user.id,trust:'self-reported'}),201);
      }else if(/^\/api\/runs\/[a-f0-9-]+$/.test(path)&&req.method==='GET'){
        const id=path.split('/').pop()!;if(!uuid.test(id))throw new HttpError(400,'Invalid run ID');
        const runs=await db('run_requests?id=eq.'+id+'&select=*') as unknown[];
        if(!runs.length)throw new HttpError(404,'Run not found');response=json(runs[0]);
      }else if(path==='/api/leaderboards'&&req.method==='GET')response=json({objective:[],preference:[],reason:'Cloud ranking publication requires an operator-controlled verified pipeline. Local evidence is never official.'});
      else throw new HttpError(404,'Route unavailable in cloud metadata mode; use the complete local application');
    }
  }catch(error){response=json({error:error instanceof HttpError?error.message:'Request failed',request_id:requestId},error instanceof HttpError?error.status:500)}
  const out=new Response(response.body,response);out.headers.set('x-request-id',requestId);out.headers.set('x-content-type-options','nosniff');out.headers.set('cache-control','no-store');out.headers.set('content-security-policy',"default-src 'none'; frame-ancestors 'none'");
  if(origin===env.ALLOWED_ORIGIN){out.headers.set('access-control-allow-origin',origin);out.headers.set('vary','Origin');out.headers.set('access-control-allow-headers','authorization,content-type');out.headers.set('access-control-allow-methods','GET,POST,OPTIONS')}
  return out;
}
export default {fetch(request:Request,env:Env){return handle(request,env)}};
