import * as THREE from "three";
import {
  box,
  cylinder,
  material,
  palette as p,
  textLabel,
  type EquipmentModel,
} from "./primitives";

export function createAhuModel(accent: string): EquipmentModel {
  const group = new THREE.Group();
  const chassis = box(group, [3.7, 0.19, 1.55], [0, 0.21, 0], p.frame);
  chassis.name = "Structural base";
  for (const x of [-1.55, 1.55])
    for (const z of [-0.53, 0.53])
      box(group, [0.22, 0.25, 0.22], [x, 0.075, z], p.dark);
  box(group, [3.65, 1.55, 0.07], [0, 1.05, -0.73], p.panel);
  box(group, [0.08, 1.58, 1.5], [-1.8, 1.05, 0], p.frame);
  box(group, [0.08, 1.58, 1.5], [1.8, 1.05, 0], p.frame);
  for (const x of [-0.58, 0.64])
    box(group, [0.045, 1.52, 1.45], [x, 1.05, 0], p.frame);
  const top = box(group, [3.72, 0.13, 1.6], [0, 1.88, 0], p.panel);
  const panels = new THREE.Group();
  group.add(panels);
  for (const [x, label] of [
    [-1.2, "FILTER"],
    [0.01, "COIL"],
    [1.23, "FAN"],
  ] as [number, string][]) {
    box(panels, [1.1, 1.36, 0.075], [x, 1.06, 0.75], p.panel);
    box(panels, [0.065, 0.3, 0.065], [x + 0.4, 1.08, 0.82], p.dark);
    textLabel(panels, label, [x, 0.55, 0.795], 0.52, p.frame);
    for (const sx of [-0.45, 0.45])
      for (const sy of [0.47, 1.64])
        cylinder(panels, 0.022, 0.018, [x + sx, sy, 0.797], p.frame);
  }
  for (let i = 0; i < 13; i++)
    box(
      group,
      [0.044, 1.25, 1.2],
      [-1.66 + i * 0.072, 1.04, 0],
      i % 2 ? p.light : "#aabcae",
      0.007,
    );
  for (let i = 0; i < 13; i++)
    box(
      group,
      [0.037, 1.2, 1.17],
      [-0.47 + i * 0.075, 1.03, 0],
      p.copper,
      0.004,
    );
  for (const y of [0.52, 1.55]) {
    const pipe = cylinder(group, 0.058, 1.03, [0.03, y, 0.63], p.copper);
    pipe.rotation.set(0, 0, Math.PI / 2);
  }
  cylinder(group, 0.56, 0.17, [1.23, 1.07, 0.18], p.frame);
  const fan = new THREE.Group();
  fan.position.set(1.23, 1.07, 0.3);
  group.add(fan);
  cylinder(fan, 0.12, 0.14, [0, 0, 0.1], p.light);
  for (let i = 0; i < 7; i++) {
    const blade = box(fan, [0.15, 0.45, 0.025], [0, 0, 0], p.panel, 0.035);
    const angle = (i * Math.PI * 2) / 7;
    blade.position.set(Math.sin(angle) * 0.28, Math.cos(angle) * 0.28, 0.015);
    blade.rotation.z = -angle + 0.34;
  }
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(0.55, 0.026, 10, 48),
    material(p.light),
  );
  ring.position.set(1.23, 1.07, 0.38);
  group.add(ring);
  for (let i = 0; i < 9; i++)
    box(
      group,
      [0.014, 1.15, 0.018],
      [0.71 + i * 0.13, 1.07, 0.42],
      p.frame,
      0.002,
    );
  for (const side of [-1, 1]) {
    box(group, [0.42, 0.85, 0.95], [side * 2.02, 1.12, 0], p.light);
    box(group, [0.035, 0.72, 0.82], [side * 2.245, 1.12, 0], p.dark);
    for (let i = 0; i < 7; i++)
      box(
        group,
        [0.04, 0.045, 0.76],
        [side * 2.27, 0.83 + i * 0.095, 0],
        p.panel,
        0.006,
      );
  }
  const controller = box(
    group,
    [0.48, 0.54, 0.13],
    [1.38, 1.46, 0.87],
    p.frame,
  );
  box(controller, [0.29, 0.16, 0.015], [0, 0.06, 0.075], accent);
  textLabel(controller, "ALTO", [0, -0.13, 0.077], 0.23, p.light);
  textLabel(group, "AIR HANDLING UNIT", [0, 0.215, 0.79], 1.25);
  return {
    group,
    fan,
    setExploded(enabled) {
      top.position.y = enabled ? 2.45 : 1.88;
      top.position.z = enabled ? -1.25 : 0;
      panels.visible = !enabled;
    },
  };
}
