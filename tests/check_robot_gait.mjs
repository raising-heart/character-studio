import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

const file = process.argv[2];
if (!file) throw new Error('Usage: npm run test:gait -- /path/to/freshly-generated/Scout.glb');
const bytes = fs.readFileSync(file);
const gltf = await new Promise((resolve, reject) => new GLTFLoader().parse(
  bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '', resolve, reject));
gltf.scene.updateMatrixWorld(true);
const legs = ['L', 'R'].map(side => {
  const upper = gltf.scene.getObjectByName('UpperLeg' + side);
  const lower = gltf.scene.getObjectByName('LowerLeg' + side);
  const foot = gltf.scene.getObjectByName('Foot' + side);
  assert(upper?.isBone && lower?.isBone && foot?.isBone, 'Both complete leg chains must exist');
  return {side, upper, lower, foot, kneeBind: lower.quaternion.clone(), footBind: foot.getWorldQuaternion(new THREE.Quaternion())};
});
const mixer = new THREE.AnimationMixer(gltf.scene), reports = [];
for (const name of ['Walk', 'Run']) {
  const clip = gltf.animations.find(c => c.name === name); assert(clip);
  mixer.stopAllAction(); mixer.clipAction(clip).reset().play();
  const samples = legs.map(leg => ({side: leg.side, leadingChecks: 0, minKnee: Infinity, maxKnee: -Infinity, maxFootPitch: 0}));
  for (let index = 0; index <= 64; index++) {
    mixer.setTime(clip.duration * index / 64); gltf.scene.updateMatrixWorld(true);
    for (let side = 0; side < legs.length; side++) {
      const leg = legs[side], record = samples[side];
      const delta = leg.kneeBind.clone().invert().multiply(leg.lower.quaternion);
      const kneeAngle = 2 * Math.atan2(delta.x, delta.w);
      assert(kneeAngle >= -.01 && kneeAngle < 1.4, `${name} ${leg.side}: knee hyperextension`);
      record.minKnee = Math.min(record.minKnee, kneeAngle); record.maxKnee = Math.max(record.maxKnee, kneeAngle);
      const hip = leg.upper.getWorldPosition(new THREE.Vector3());
      const knee = leg.lower.getWorldPosition(new THREE.Vector3());
      const ankle = leg.foot.getWorldPosition(new THREE.Vector3());
      if (knee.z > hip.z + .04) {
        assert(ankle.y < knee.y - .1, `${name} ${leg.side}: leading ankle folded above knee`);
        record.leadingChecks++;
      }
      const footDelta = leg.foot.getWorldQuaternion(new THREE.Quaternion()).multiply(leg.footBind.clone().invert());
      const pitch = 2 * Math.acos(Math.min(1, Math.abs(footDelta.w)));
      assert(pitch < .35, `${name} ${leg.side}: foot sole pitched toward the camera`);
      record.maxFootPitch = Math.max(record.maxFootPitch, pitch);
    }
  }
  for (const sample of samples) {assert(sample.leadingChecks > 12, 'Both leading legs must be checked'); assert(sample.maxKnee > (name === 'Run' ? .8 : .35), 'Recovery knee must flex');}
  reports.push({clip: name, samplesPerSide: 65, legs: samples});
}
console.log(JSON.stringify({passed: true, checks: ['both leg chains', 'backward knee flexion', 'leading ankle below knee', 'controlled foot pitch', 'full-cycle sampling'], reports}, null, 2));
