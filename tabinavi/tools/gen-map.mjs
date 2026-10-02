import {readFileSync, writeFileSync} from 'fs';
import * as topo from 'topojson-client';
import {geoEqualEarth, geoPath, geoGraticule10} from 'd3-geo';
const w = JSON.parse(readFileSync('node_modules/world-atlas/countries-110m.json','utf8'));
const feats = topo.feature(w, w.objects.countries).features.filter(f=>String(f.id)!=='010');
const proj = geoEqualEarth().rotate([-155,0]).fitExtent([[6,6],[994,494]], {type:'Sphere'});
const path = geoPath(proj).digits(1);
const land = feats.map(f=>path(f)).filter(Boolean).join('');
const grat = path(geoGraticule10());
const sphere = path({type:'Sphere'});
const k = proj.scale(), [tx,ty] = proj.translate();
// parity check
const A1=1.340264,A2=-0.081106,A3=0.000893,A4=0.003796,M=Math.sqrt(3)/2;
function mine(lon,lat){const l=(((lon-155+540)%360)-180)*Math.PI/180,p=lat*Math.PI/180;const t=Math.asin(M*Math.sin(p)),t2=t*t,t6=t2*t2*t2;
 const x=l*Math.cos(t)/(M*(A1+3*A2*t2+t6*(7*A3+9*A4*t2)));const y=t*(A1+A2*t2+t6*(A3+A4*t2));return [tx+k*x,ty-k*y];}
for (const [lo,la] of [[135,35],[-157.9,21.3],[2.35,48.86],[151.2,-33.9],[-74,40.7],[0,0],[-9.1,38.7]]) console.log(lo,la,proj([lo,la]).map(v=>v.toFixed(2)).join(','),mine(lo,la).map(v=>v.toFixed(2)).join(','));
const yTop=mine(0,84)[1], yBot=mine(0,-57)[1];
console.log('k',k,'t',tx,ty,'yTop',yTop,'yBot',yBot,'land bytes',land.length,'grat',grat.length,'sphere',sphere.length);
writeFileSync('../data/land.txt',land);writeFileSync('../data/grat.txt',grat);writeFileSync('../data/sphere.txt',sphere);
writeFileSync('../data/proj.json',JSON.stringify({k,tx,ty,yTop,yBot}));
