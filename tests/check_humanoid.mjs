import fs from 'node:fs';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {GLTFLoader} from 'three/examples/jsm/loaders/GLTFLoader.js';

const files=process.argv.slice(2);
assert(files.length, 'Pass one or more final humanoid GLB paths.');
const reports=[];
for(const file of files){
 const data=fs.readFileSync(file);
 const gltf=await new Promise((resolve,reject)=>new GLTFLoader().parse(data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength),'',resolve,reject));
 assert.deepEqual(gltf.animations.map(c=>c.name).sort(),['Idle','Jump','Roll','Run','Walk']);
 const meshes=[],bones=[];
 gltf.scene.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o);if(o.isBone)bones.push(o);});
 assert(meshes.length>=5&&bones.length===16,'Expected modular skin and humanoid skeleton');
 const bone=name=>{const result=gltf.scene.getObjectByName(name.replaceAll('.',''))||gltf.scene.getObjectByName(name);assert(result?.isBone,name);return result;};
 const root=bone('Root'),mixer=new THREE.AnimationMixer(gltf.scene);
 const world=name=>bone(name).getWorldPosition(new THREE.Vector3());
 function pose(){
  gltf.scene.updateMatrixWorld(true);const bounds=new THREE.Box3();
  for(const mesh of meshes){mesh.skeleton.update();const positions=mesh.geometry.attributes.position;
   for(let i=0;i<positions.count;i++){const p=new THREE.Vector3().fromBufferAttribute(positions,i);mesh.applyBoneTransform(i,p);p.applyMatrix4(mesh.matrixWorld);assert(p.toArray().every(Number.isFinite),'Finite deformed vertices');bounds.expandByPoint(p);}}
  return {bounds,matrices:bones.flatMap(b=>b.matrixWorld.elements),rootY:root.position.y};
 }
 pose();
 const rootBind=root.getWorldQuaternion(new THREE.Quaternion());
 for(const side of ['L','R'])assert(Math.abs(world('Hand.'+side).y-world('UpperArm.'+side).y)<.015,'Bind pose must have T-pose arms');
 const clips=[];
 for(const clip of gltf.animations){
  mixer.stopAllAction();const once=['Jump','Roll'].includes(clip.name);
  const action=mixer.clipAction(clip).reset().setLoop(once?THREE.LoopOnce:THREE.LoopRepeat,once?1:Infinity);action.clampWhenFinished=true;action.play();
  mixer.setTime(0);const initial=pose(),samples=[];
  for(let i=0;i<=64;i++){
   mixer.setTime(clip.duration*i/64);const sample=pose();samples.push(sample);
   assert(sample.bounds.min.y>-.012,`${clip.name} ground clearance`);
   if(['Idle','Walk','Run'].includes(clip.name))for(const side of ['L','R']){
    assert(world('Hand.'+side).y<world('UpperArm.'+side).y-.15,'T-pose retarget must lower both arms');
    const knee=world('LowerLeg.'+side),hip=world('UpperLeg.'+side),ankle=world('Foot.'+side);
    assert(knee.distanceTo(hip)>.1&&knee.distanceTo(ankle)>.1,'Both knee/shin chains retain length');
   }
  }
  const end=samples.at(-1),delta=Math.max(...end.matrices.map((v,i)=>Math.abs(v-initial.matrices[i])));
  assert(delta<2e-4,`${clip.name} returns to its initial pose`);
  if(clip.name==='Jump')assert(Math.max(...samples.map(p=>p.rootY))-initial.rootY>.25,'Jump visibly lifts');
  if(clip.name==='Roll'){action.paused=false;mixer.setTime(clip.duration/2);pose();const rotation=root.getWorldQuaternion(new THREE.Quaternion()).multiply(rootBind.clone().invert());assert(new THREE.Vector3(0,1,0).applyQuaternion(rotation).y<-.9,'Full roll reaches inverted midpoint');}
  if(once){mixer.setTime(clip.duration*2);const held=pose();assert(Math.max(...held.matrices.map((v,i)=>Math.abs(v-end.matrices[i])))<1e-4,'One-shot holds completion');}
  clips.push({name:clip.name,duration:clip.duration,endpointDelta:delta,minGroundY:Math.min(...samples.map(p=>p.bounds.min.y))});
 }
 assert(clips.find(c=>c.name==='Run').duration<clips.find(c=>c.name==='Walk').duration,'Run cadence faster than Walk');
 reports.push({file,meshes:meshes.length,bones:bones.length,clips});
}
console.log(JSON.stringify({passed:true,checks:['T-pose bind','neutral-pose-aware arm animation','both knee/shin chains','finite skinned vertices','64 samples per clip','ground clearance','loop and landing endpoints','Jump lift','full Roll','one-shot hold'],assets:reports},null,2));
