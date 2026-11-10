import {afterEach,beforeEach,describe,it,expect,vi} from 'vitest';
import {api} from '../src/api';
beforeEach(()=>localStorage.clear());
afterEach(()=>vi.unstubAllGlobals());
it('GET and JSON mutation construction retain only current session',async()=>{
 localStorage.setItem('token','fixture-session');const fetcher=vi.fn(async()=>Response.json({ok:true}));vi.stubGlobal('fetch',fetcher);
 expect(await api('/me')).toEqual({ok:true});expect(fetcher.mock.calls[0][1].method).toBe('GET');expect(fetcher.mock.calls[0][1].headers.Authorization).toBe('Bearer fixture-session');
 await api('/runs',{});expect(fetcher.mock.calls[1][1].method).toBe('POST');expect(fetcher.mock.calls[1][1].body).toBe('{}');
});
it('current 401 expires session; auth errors do not',async()=>{
 const listener=vi.fn();window.addEventListener('praxis-session-expired',listener);localStorage.setItem('token','fixture-session');
 vi.stubGlobal('fetch',vi.fn(async()=>Response.json({error:'expired'},{status:401})));
 await expect(api('/me')).rejects.toThrow('expired');expect(listener).toHaveBeenCalledOnce();
 await expect(api('/auth/login',{})).rejects.toThrow('expired');expect(listener).toHaveBeenCalledOnce();window.removeEventListener('praxis-session-expired',listener);
});
it('old 401 does not revoke a replaced session',async()=>{
 localStorage.setItem('token','old-session');let resolve!:(r:Response)=>void;vi.stubGlobal('fetch',vi.fn(()=>new Promise<Response>(r=>resolve=r)));
 const listener=vi.fn();window.addEventListener('praxis-session-expired',listener);const pending=api('/me');localStorage.setItem('token','new-session');resolve(Response.json({}, {status:401}));
 await expect(pending).rejects.toThrow('Request failed');expect(listener).not.toHaveBeenCalled();window.removeEventListener('praxis-session-expired',listener);
});
it('malformed and unavailable responses surface errors',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response('not json')));await expect(api('/me')).rejects.toThrow('invalid JSON');
 vi.stubGlobal('fetch',vi.fn().mockRejectedValue(Error('offline')));await expect(api('/me')).rejects.toThrow('offline');
});
