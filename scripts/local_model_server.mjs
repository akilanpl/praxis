/** Real, free CPU inference. No fixture answers, output repair or model API charges. */
import { createServer } from 'node:http';
import { pipeline, env } from '@huggingface/transformers';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mkdirSync } from 'node:fs';
const root=resolve(fileURLToPath(new URL('..',import.meta.url)));
env.cacheDir=resolve(root,'work/model-cache');
mkdirSync(env.cacheDir,{recursive:true});
const models={'onnx-community/SmolLM2-135M-Instruct-ONNX':'b8a5c0f183b78c55955a5364f610c36668b5e681','onnx-community/SmolLM2-360M-Instruct-ONNX':'fe7c7db4c8921c9e3fa1c65cfd296fb3b1b1a8f9'};
const model=process.env.PRAXIS_LOCAL_MODEL||'onnx-community/SmolLM2-135M-Instruct-ONNX';
if(!models[model])throw Error('Only the pinned small acceptance models are supported');
const revision=models[model];
const port=Number(process.env.PRAXIS_MODEL_PORT||8788);
console.log('Loading real model on CPU:',model,'revision',revision,'dtype q4. No paid API.');
const generator=await pipeline('text-generation',model,{dtype:'q4',device:'cpu',revision});
console.log('Model loaded.');
let busy=false;
function json(res,status,value){res.writeHead(status,{'Content-Type':'application/json','X-Content-Type-Options':'nosniff'});res.end(JSON.stringify(value));}
const server=createServer(async(req,res)=>{
 if(!['127.0.0.1','localhost'].includes((req.headers.host||'').split(':')[0]))return json(res,403,{error:'Loopback host required'});
 if(req.method==='GET'&&req.url==='/v1/models')return json(res,200,{data:[{id:model,object:'model',revision,dtype:'q4',runtime:'Transformers.js CPU; real inference'}]});
 if(req.method==='GET'&&req.url==='/health')return json(res,200,{status:'ok',model,revision,real_inference:true});
 if(req.method!=='POST'||req.url!=='/v1/chat/completions')return json(res,404,{error:'Route not found'});
 if(busy)return json(res,429,{error:'One CPU inference at a time'});
 try{
  let bytes=0,parts=[];for await(const part of req){bytes+=part.length;if(bytes>262144)return json(res,413,{error:'Request too large'});parts.push(part);}
  const body=JSON.parse(Buffer.concat(parts).toString());
  if(body.model!==model||!Array.isArray(body.messages)||body.messages.length>32)return json(res,400,{error:'Use the advertised model ID and bounded messages'});
  if(body.temperature&&body.temperature!==0)return json(res,400,{error:'This acceptance endpoint supports deterministic temperature zero only'});
  if(body.stream)return json(res,400,{error:'Streaming unsupported by this small local endpoint'});
  for(const m of body.messages)if(!['user','assistant','system'].includes(m.role)||typeof m.content!=='string')return json(res,400,{error:'Invalid message'});
  busy=true;
  const prompt=generator.tokenizer.apply_chat_template(body.messages,{tokenize:false,add_generation_prompt:true});
  const start=performance.now();
  const result=await generator(prompt,{max_new_tokens:Math.min(Math.max(Number(body.max_tokens)||128,1),256),do_sample:false,return_full_text:false});
  const content=result[0].generated_text;
  if(typeof content!=='string')throw Error('Unexpected generator output');
  const inputTokens=generator.tokenizer(prompt).input_ids.data.length;
  const outputTokens=generator.tokenizer(content,{add_special_tokens:false}).input_ids.data.length;
  json(res,200,{id:crypto.randomUUID(),object:'chat.completion',model,model_revision:revision,runtime:'transformers.js CPU q4',inference_ms:performance.now()-start,choices:[{index:0,message:{role:'assistant',content},finish_reason:'stop'}],usage:{prompt_tokens:inputTokens,completion_tokens:outputTokens,total_tokens:inputTokens+outputTokens}});
 }catch(error){console.error('Inference failed:',error.message);json(res,500,{error:'Real local inference failed; inspect runner log'});}
 finally{busy=false;}
});
server.listen(port,'127.0.0.1',()=>console.log('Real local model: http://127.0.0.1:'+port+'/v1'));
for(const signal of ['SIGTERM','SIGINT'])process.on(signal,()=>server.close(()=>process.exit(0)));
