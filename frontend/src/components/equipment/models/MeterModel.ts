import * as THREE from "three";
import {
  box,
  cylinder,
  palette as p,
  textLabel,
  type EquipmentModel,
} from "./primitives";
export function createMeterModel(accent: string): EquipmentModel {
  const group = new THREE.Group();
  group.position.y = 0.45;
  box(group, [1.7, 1.7, 0.72], [0, 0.75, 0], p.light, 0.07);
  box(group, [1.45, 1.4, 0.06], [0, 0.8, 0.4], p.frame, 0.04);
  box(group, [1.06, 0.48, 0.025], [0, 1.02, 0.442], "#b9ce9b", 0.03);
  textLabel(group, "kW / kWh", [0, 1.03, 0.46], 0.91, p.dark);
  textLabel(group, "ENERGY METER", [0, 1.46, 0.442], 0.92);
  for (const x of [-0.43, 0, 0.43])
    cylinder(group, 0.065, 0.038, [x, 0.53, 0.46], p.panel);
  cylinder(group, 0.033, 0.025, [0.59, 1.28, 0.46], accent);
  const terminal = new THREE.Group();
  group.add(terminal);
  for (let i = 0; i < 6; i++) {
    box(terminal, [0.16, 0.28, 0.28], [-0.6 + i * 0.24, -0.21, 0], p.frame);
    cylinder(terminal, 0.033, 0.017, [-0.6 + i * 0.24, -0.2, 0.15], p.copper);
  }
  return {
    group,
    setExploded(enabled) {
      terminal.position.y = enabled ? -0.45 : 0;
    },
  };
}
