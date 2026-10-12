import fs from 'node:fs';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {GLTFLoader} from 'three/examples/jsm/loaders/GLTFLoader.js';

const files = process.argv.slice(2);
assert(files.length, 'Pass one or more rigged base-body GLBs.');
const reports = [];
for (const file of files) {
  const data = fs.readFileSync(file);
  const gltf = await new Promise((resolve, reject) => new GLTFLoader().parse(data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength), '', resolve, reject));
  const meshes = [], bones = [];
  gltf.scene.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); if (o.isBone) bones.push(o); });
  assert.equal(meshes.length, 1, 'One body skin');
  assert.equal(bones.length, 16, 'Neutral humanoid skeleton');
  assert.deepEqual(gltf.animations.map(c => c.name).sort(), ['CheckElbows', 'CheckHipSpread', 'CheckKnees', 'CheckShoulders', 'CheckTwist']);
  const mesh = meshes[0], pos = mesh.geometry.attributes.position;
  const bone = name => { const b = gltf.scene.getObjectByName(name.replaceAll('.', '')) || gltf.scene.getObjectByName(name); assert(b?.isBone, name); return b; };
  const world = name => bone(name).getWorldPosition(new THREE.Vector3());
  function vertices() {
    gltf.scene.updateMatrixWorld(true); mesh.skeleton.update();
    const result = [];
    for (let i = 0; i < pos.count; i++) {
      const p = new THREE.Vector3().fromBufferAttribute(pos, i);
      mesh.applyBoneTransform(i, p); p.applyMatrix4(mesh.matrixWorld);
      assert(p.toArray().every(Number.isFinite)); result.push(p);
      const w = mesh.geometry.attributes.skinWeight;
      const sum = w.getX(i) + w.getY(i) + w.getZ(i) + w.getW(i);
      assert(Math.abs(sum - 1) < 1e-5, 'Normalised weights');
    }
    return result;
  }
  const bind = vertices();
  for (const side of ['L', 'R']) assert(Math.abs(world('Hand.' + side).y - world('UpperArm.' + side).y) < 1e-5, 'Level T-pose arms');
  const coordinates = new Set(bind.map(p => p.toArray().map(v => Math.round(v * 1e5)).join(',')));
  for (const p of bind) assert(coordinates.has([-p.x, p.y, p.z].map(v => Math.round(v * 1e5)).join(',')), 'Symmetric rest geometry');
  const index = mesh.geometry.index;
  assert(index, 'Indexed triangles');
  const lengths = [];
  for (let i = 0; i < index.count; i += 3) {
    const ids = [index.getX(i), index.getX(i + 1), index.getX(i + 2)];
    for (let k = 0; k < 3; k++) lengths.push([ids[k], ids[(k + 1) % 3], bind[ids[k]].distanceTo(bind[ids[(k + 1) % 3]])]);
  }
  const mixer = new THREE.AnimationMixer(gltf.scene), poses = [];
  for (const clip of gltf.animations) {
    mixer.stopAllAction(); mixer.clipAction(clip).reset().play(); mixer.setTime(clip.duration * .5);
    const deformed = vertices();
    let minRatio = Infinity, maxRatio = 0, maxEdge = null;
    for (const [a, b, original] of lengths) {
      if (original < 1e-6) continue;
      const ratio = deformed[a].distanceTo(deformed[b]) / original;
      minRatio = Math.min(minRatio, ratio);
      if (ratio > maxRatio) { maxRatio = ratio; maxEdge = {a: bind[a].toArray(), b: bind[b].toArray()}; }
    }
    assert(minRatio > .20 && maxRatio < 2.6, `${clip.name}: severe edge collapse/stretch ${minRatio}..${maxRatio}; ${JSON.stringify(maxEdge)}`);
    assert(Math.max(...deformed.map((p, i) => p.distanceTo(bind[i]))) > .04, 'Study must actually deform the body');
    for (const side of ['L', 'R']) {
      if (clip.name === 'CheckShoulders') assert(world('Hand.' + side).y > world('UpperArm.' + side).y + .25);
      if (clip.name === 'CheckElbows') assert(world('Hand.' + side).z > world('LowerArm.' + side).z + .15);
      if (clip.name === 'CheckHipSpread') assert(Math.abs(world('Foot.' + side).x) > Math.abs(world('UpperLeg.' + side).x) + .15);
      if (clip.name === 'CheckKnees') {
        const a = world('UpperLeg.' + side).sub(world('LowerLeg.' + side)).normalize();
        const b = world('Foot.' + side).sub(world('LowerLeg.' + side)).normalize();
        const angle = Math.acos(THREE.MathUtils.clamp(a.dot(b), -1, 1));
        assert(angle < Math.PI * .7 && angle > Math.PI * .3, 'Knee actually bends');
      }
    }
    poses.push({name: clip.name, minEdgeRatio: minRatio, maxEdgeRatio: maxRatio});
  }
  reports.push({file, bones: bones.length, bodySkins: meshes.length, triangles: index.count / 3, poses});
}
console.log(JSON.stringify({passed: true, scope: 'Skin integrity, symmetry and observable joint poses; visual quality still requires render inspection.', assets: reports}, null, 2));
