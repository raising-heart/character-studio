# Animal design and motion

Start with the species and body plan: quadruped, bird, fish, snake, insect, or a fictional creature. Use a species-appropriate silhouette and gait rather than adapting a humanoid skeleton without checking it. State whether the result is a segmented stylization or a continuous skinned animal.

The bundled `build_quadruped.py` is a segmented fox/dog/cat reference. It has a torso, neck/head, two tail bones, four upper/lower legs and paws, with Idle/Walk/Run/Jump. Species choices change muzzle and ears; they are not anatomically accurate complete species generators. Build a custom silhouette for the actual brief. Height is a reference scale parameter; measure exported dimensions, especially for different ears/body proportions.

```text
blender --background --factory-startup --python-exit-code 1 --python <skill-root>/scripts/build_quadruped.py -- --output <new-directory> --name Fox --species fox --height 0.9
```

Keep `build_robot.py` alongside it for shared material, argument, staging and export helpers. Static and no-render modes are supported. The script refuses existing outputs unless `--overwrite` is explicit.

For continuous skin, blend weights around shoulders, hips and the neck, check belly distortion and paw volume, and separate deformation bones from controls. Hooves, digitigrade hocks, wings, fins and many-legged bodies need tailored joint chains. Do not imply the bundled quadruped auto-rigs arbitrary animals.

Check footfall order and contact: a readable walk, trot and gallop have different patterns. The reference Walk uses diagonal pairs and the Run uses a simplified bound; neither locks paws or guarantees biological accuracy. Review body bounce, spine flexion, tail lag, ears, head stability and limb intersections from the gameplay camera. Roll is not included by default for quadrupeds; author a species-appropriate roll/lie-down if requested, rather than transferring the robot's forward tumble.

Jump includes baked vertical lift. Follow the rigging reference to avoid combining it with physics jump displacement. Test exported clip names, all four limbs and the tail in a runtime preview; retain the user's existing rig and animations during edits.
