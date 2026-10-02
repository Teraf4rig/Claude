import {readFileSync, writeFileSync} from 'fs';
import * as topo from 'topojson-client';
import {geoContains} from 'd3-geo';
const w = JSON.parse(readFileSync('node_modules/world-atlas/land-110m.json','utf8'));
const land = topo.feature(w, w.objects.land);
const S=1.25, out=[];let n=0;
for(let lat=-56;lat<=82;lat+=S){
  const step=S/Math.max(.18,Math.cos(lat*Math.PI/180));
  for(let lon=-180;lon<180;lon+=step){
    n++; if(geoContains(land,[lon,lat])){
      const a=Math.round((lat+90)*2), b=Math.round((((lon+180)%360)+360)%360*2);
      out.push((a*721+b).toString(36).padStart(4,'0'));
    }
  }
}
writeFileSync('../data/globe.txt',out.join(''));
console.log('samples',n,'land dots',out.length,'bytes',out.join('').length);
