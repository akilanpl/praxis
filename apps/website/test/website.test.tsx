import {it,expect} from 'vitest';
import {waitFor} from '@testing-library/react';
it('renders repository-derived coverage and working architectural anchors',async()=>{
 document.body.innerHTML='<div id="root"></div>';await import('../src/main');
 await waitFor(()=>expect(document.querySelectorAll('.suite-row').length).toBe(6));
 expect(document.querySelector('.facts')?.textContent).toContain('40');
 for(const a of document.querySelectorAll<HTMLAnchorElement>('a[href^="#"]'))if(a.hash)expect(document.getElementById(a.hash.slice(1))).not.toBeNull();
 expect(document.querySelector('#evidence')?.textContent).toContain('0% task pass rate');
});
