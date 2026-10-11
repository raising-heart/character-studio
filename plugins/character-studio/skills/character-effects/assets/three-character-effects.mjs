/** Bounded starter VFX. Supply the Three.js namespace used by the host project. */
export function createCharacterEffects(THREE, scene, options = {}) {
  const capacity = options.maxParticles ?? 256;
  if (!Number.isInteger(capacity) || capacity < 1 || capacity > 4096) throw new RangeError('maxParticles must be 1..4096');
  if (!scene?.isObject3D) throw new TypeError('scene must be an Object3D');
  let seed = options.seed ?? 1;
  if (!Number.isInteger(seed)) throw new TypeError('seed must be an integer');
  let reduced = Boolean(options.reducedMotion), disposed = false, elapsed = 0, dropped = 0;
  const emitters = new Map(), auras = new Map(), trails = new Map();
  const root = new THREE.Group(); root.name = 'CharacterEffects'; scene.add(root);
  const positions = new Float32Array(capacity * 3), velocities = new Float32Array(capacity * 3);
  const colors = new Float32Array(capacity * 3), sizes = new Float32Array(capacity);
  const alpha = new Float32Array(capacity), active = new Uint8Array(capacity);
  const ages = new Float32Array(capacity), lives = new Float32Array(capacity);
  const baseSizes = new Float32Array(capacity), baseAlpha = new Float32Array(capacity);
  const acceleration = new Float32Array(capacity), kinds = new Array(capacity);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  geometry.setAttribute('effectSize', new THREE.BufferAttribute(sizes, 1));
  geometry.setAttribute('effectAlpha', new THREE.BufferAttribute(alpha, 1));
  const material = new THREE.ShaderMaterial({ transparent: true, depthWrite: false,
    uniforms: { pixelRatio: { value: Math.min(2, options.pixelRatio ?? 1) } },
    vertexShader: `attribute float effectSize; attribute float effectAlpha;
      varying vec3 vColor; varying float vAlpha; uniform float pixelRatio;
      void main() { vColor = color; vAlpha = effectAlpha;
        vec4 p = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = effectSize * pixelRatio * clamp(3.0 / max(0.1, -p.z), 0.4, 3.0);
        gl_Position = projectionMatrix * p; }`,
    fragmentShader: `varying vec3 vColor; varying float vAlpha;
      void main() { float r = length(gl_PointCoord - vec2(0.5));
        float a = vAlpha * (1.0 - smoothstep(0.12, 0.5, r));
        if (a < 0.003) discard; gl_FragColor = vec4(vColor, a); }`,
    vertexColors: true });
  const points = new THREE.Points(geometry, material); points.frustumCulled = false; root.add(points);
  const scratch = new THREE.Vector3();
  const profiles = {
    sparks: { color: 0xffc857, life: .65, size: 8, opacity: .95, speed: 1.8, gravity: -3.5 },
    smoke: { color: 0x9da6ad, life: 1.5, size: 24, opacity: .30, speed: .20, gravity: .20 },
    fire: { color: 0xffa52e, life: .60, size: 19, opacity: .75, speed: .38, gravity: .50 },
    dust: { color: 0xd6b995, life: .75, size: 13, opacity: .45, speed: .45, gravity: -.15 },
    magic: { color: 0x62ddff, life: 1.0, size: 11, opacity: .80, speed: .60, gravity: .05 }
  };
  function ready() { if (disposed) throw new Error('Effects have been disposed'); }
  function random() {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  }
  function finite(value, name, min = 0, max = Infinity) {
    if (!Number.isFinite(value) || value < min || value > max) throw new RangeError(`${name} is invalid`);
    return value;
  }
  function profile(kind) { if (!profiles[kind]) throw new RangeError(`Unknown effect kind: ${kind}`); return profiles[kind]; }
  function anchorPosition(anchor, offset, out = scratch) {
    if (!anchor?.isObject3D) throw new TypeError('anchor must be an Object3D');
    anchor.updateWorldMatrix(true, false);
    out.set(...offset).applyMatrix4(anchor.matrixWorld);
    scene.updateWorldMatrix(true, false); scene.worldToLocal(out);
    return out;
  }
  function offsetOf(config) {
    const offset = config.offset ?? [0, 0, 0];
    if (!Array.isArray(offset) || offset.length !== 3 || !offset.every(Number.isFinite)) throw new TypeError('offset must be three finite numbers');
    return [...offset];
  }
  function dirty() { for (const attr of Object.values(geometry.attributes)) attr.needsUpdate = true; }
  function clearParticles() { active.fill(0); alpha.fill(0); dirty(); }
  function resetTrail(trail) { trail.count = 0; trail.credit = 0; trail.geometry.setDrawRange(0, 0); }
  function burst(kind, position, count = 24) {
    ready(); const p = profile(kind);
    if (!position?.isVector3 || ![position.x, position.y, position.z].every(Number.isFinite)) throw new TypeError('position must be a finite Vector3 in scene coordinates');
    if (!Number.isInteger(count) || count < 0 || count > 65536) throw new RangeError('count must be 0..65536');
    if (reduced) return 0;
    const rgb = new THREE.Color(p.color);
    let emitted = 0;
    for (let i = 0; i < capacity && emitted < count; i++) {
      if (active[i]) continue;
      const index = i * 3, angle = random() * Math.PI * 2;
      const radius = Math.sqrt(random()) * p.speed;
      const upward = kind === 'fire' || kind === 'smoke';
      positions[index] = position.x + (random() - .5) * .04;
      positions[index + 1] = position.y;
      positions[index + 2] = position.z + (random() - .5) * .04;
      velocities[index] = Math.cos(angle) * radius * (upward ? .35 : 1);
      velocities[index + 1] = upward ? p.speed * (.7 + random()) : p.speed * (.2 + random() * .8);
      velocities[index + 2] = Math.sin(angle) * radius * (upward ? .35 : 1);
      colors.set([rgb.r, rgb.g, rgb.b], index);
      ages[i] = 0; lives[i] = p.life * (.8 + random() * .4);
      sizes[i] = baseSizes[i] = p.size * (.8 + random() * .4);
      alpha[i] = baseAlpha[i] = p.opacity;
      acceleration[i] = p.gravity; kinds[i] = kind; active[i] = 1; emitted++;
    }
    dropped += count - emitted; dirty(); return emitted;
  }
  function setEmitter(name, config) {
    ready(); profile(config.kind);
    if (!config.anchor?.isObject3D) throw new TypeError('Emitter anchor must be an Object3D');
    const rate = finite(config.rate ?? 24, 'rate', 0, 1024);
    emitters.set(name, { ...config, rate, offset: offsetOf(config), credit: 0 });
  }
  function removeAura(name) {
    const aura = auras.get(name); if (!aura) return;
    root.remove(aura.mesh); aura.mesh.geometry.dispose(); aura.mesh.material.dispose(); auras.delete(name);
  }
  function setAura(name, anchor, config = {}) {
    ready(); if (!anchor?.isObject3D) throw new TypeError('Aura anchor must be an Object3D');
    const radius = finite(config.radius ?? .20, 'radius', .01, 20);
    const offset = offsetOf(config);
    removeAura(name);
    const mesh = new THREE.Mesh(new THREE.TorusGeometry(radius, radius * .06, 6, 40),
      new THREE.MeshBasicMaterial({ color: config.color ?? 0x62ddff, transparent: true, opacity: .55, depthWrite: false }));
    mesh.rotation.x = Math.PI / 2; mesh.frustumCulled = false;
    root.add(mesh); auras.set(name, { mesh, anchor, offset });
  }
  function removeTrail(name) {
    const trail = trails.get(name); if (!trail) return;
    root.remove(trail.line); trail.geometry.dispose(); trail.line.material.dispose(); trails.delete(name);
  }
  function setTrail(name, anchor, config = {}) {
    ready(); if (!anchor?.isObject3D) throw new TypeError('Trail anchor must be an Object3D');
    const samples = config.samples ?? 24;
    if (!Number.isInteger(samples) || samples < 2 || samples > 256) throw new RangeError('samples must be 2..256');
    const interval = finite(config.interval ?? 1 / 30, 'interval', .005, 1);
    const teleportDistance = finite(config.teleportDistance ?? 2, 'teleportDistance', .01, 1000);
    const offset = offsetOf(config); removeTrail(name);
    const data = new Float32Array(samples * 3), opacity = new Float32Array(samples);
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(data, 3));
    geo.setAttribute('trailAlpha', new THREE.BufferAttribute(opacity, 1)); geo.setDrawRange(0, 0);
    const mat = new THREE.ShaderMaterial({ transparent: true, depthWrite: false,
      uniforms: { tint: { value: new THREE.Color(config.color ?? 0x62ddff) } },
      vertexShader: `attribute float trailAlpha; varying float a;
        void main() { a = trailAlpha; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
      fragmentShader: `uniform vec3 tint; varying float a; void main() { gl_FragColor = vec4(tint, a); }` });
    const line = new THREE.Line(geo, mat); line.frustumCulled = false; root.add(line);
    trails.set(name, { anchor, offset, interval, teleportDistance, data, opacity,
      geometry: geo, line, samples, count: 0, credit: 0 });
  }
  function update(delta) {
    ready(); finite(delta, 'delta'); const dt = Math.min(delta, .1); elapsed += dt;
    for (const aura of auras.values()) {
      aura.mesh.position.copy(anchorPosition(aura.anchor, aura.offset));
      aura.mesh.scale.setScalar(reduced ? 1 : 1 + .06 * Math.sin(elapsed * Math.PI));
      aura.mesh.material.opacity = reduced ? .35 : .48 + .07 * Math.sin(elapsed * Math.PI);
    }
    if (!reduced) {
      for (const emitter of emitters.values()) {
        emitter.credit += dt * emitter.rate;
        const count = Math.floor(emitter.credit); emitter.credit -= count;
        if (count) burst(emitter.kind, anchorPosition(emitter.anchor, emitter.offset), count);
      }
      for (let i = 0; i < capacity; i++) {
        if (!active[i]) continue;
        ages[i] += dt;
        if (ages[i] >= lives[i]) { active[i] = 0; alpha[i] = 0; continue; }
        const index = i * 3, age = ages[i] / lives[i];
        velocities[index + 1] += acceleration[i] * dt;
        for (let axis = 0; axis < 3; axis++) positions[index + axis] += velocities[index + axis] * dt;
        alpha[i] = baseAlpha[i] * (1 - age) ** 2;
        sizes[i] = baseSizes[i] * (kinds[i] === 'smoke' ? 1 + age * 1.5 : 1 - age * .4);
      }
      for (const trail of trails.values()) {
        trail.credit += dt;
        if (!dt || trail.credit < trail.interval) continue;
        trail.credit %= trail.interval;
        const pos = anchorPosition(trail.anchor, trail.offset);
        if (trail.count && pos.distanceTo(new THREE.Vector3(...trail.data.subarray(0, 3))) > trail.teleportDistance) resetTrail(trail);
        trail.data.copyWithin(3, 0, (trail.samples - 1) * 3);
        trail.data.set([pos.x, pos.y, pos.z], 0);
        trail.count = Math.min(trail.samples, trail.count + 1);
        for (let i = 0; i < trail.samples; i++) trail.opacity[i] = i < trail.count ? .8 * (1 - i / Math.max(1, trail.count - 1)) : 0;
        trail.geometry.setDrawRange(0, trail.count);
        trail.geometry.attributes.position.needsUpdate = true;
        trail.geometry.attributes.trailAlpha.needsUpdate = true;
      }
      dirty();
    }
  }
  function setReducedMotion(value) {
    ready(); reduced = Boolean(value);
    if (reduced) { clearParticles(); for (const trail of trails.values()) resetTrail(trail); }
    for (const emitter of emitters.values()) emitter.credit = 0;
    update(0);
  }
  function clear() {
    ready(); clearParticles(); for (const trail of trails.values()) resetTrail(trail);
    for (const emitter of emitters.values()) emitter.credit = 0;
  }
  function stats() { return { capacity, activeParticles: active.reduce((a, b) => a + b, 0), droppedParticles: dropped,
    emitters: emitters.size, auras: auras.size, trails: trails.size, reducedMotion: reduced, disposed }; }
  function dispose() {
    if (disposed) return;
    for (const name of [...auras.keys()]) removeAura(name);
    for (const name of [...trails.keys()]) removeTrail(name);
    emitters.clear(); geometry.dispose(); material.dispose(); scene.remove(root); disposed = true;
  }
  if (reduced) setReducedMotion(true);
  return { object: root, burst, setEmitter, removeEmitter: name => emitters.delete(name), setAura, removeAura,
    setTrail, removeTrail, update, clear, setReducedMotion, stats, dispose };
}

/** Fire cues on (previousElapsed, currentElapsed] using monotonic clip seconds. */
export function dispatchAnimationCues(previousElapsed, currentElapsed, duration, cues, callback) {
  if (![previousElapsed, currentElapsed, duration].every(Number.isFinite) || previousElapsed < 0 || duration <= 0) throw new RangeError('Clip times must be finite; duration must be positive');
  if (!Array.isArray(cues) || typeof callback !== 'function') throw new TypeError('cues and callback are required');
  for (const cue of cues) if (!Number.isFinite(cue.time) || cue.time < 0 || cue.time >= duration) throw new RangeError('cue.time must be inside the clip');
  if (currentElapsed <= previousElapsed || currentElapsed - previousElapsed > duration * 4) return 0;
  const crossed = [];
  for (let lap = Math.floor(previousElapsed / duration); lap <= Math.floor(currentElapsed / duration); lap++) {
    for (const cue of cues) { const time = lap * duration + cue.time;
      if (time > previousElapsed + 1e-9 && time <= currentElapsed + 1e-9) crossed.push({ cue, time }); }
  }
  crossed.sort((a, b) => a.time - b.time);
  for (const item of crossed.slice(0, 128)) callback(item.cue, item.time);
  return Math.min(crossed.length, 128);
}
