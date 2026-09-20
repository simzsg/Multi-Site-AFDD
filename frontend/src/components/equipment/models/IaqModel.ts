import * as THREE from "three";
import {
  box,
  cylinder,
  palette as p,
  textLabel,
  type EquipmentModel,
} from "./primitives";
export function createIaqModel(accent: string): EquipmentModel {
  const group = new THREE.Group();
  group.position.y = 0.5;
  box(group, [1.5, 1.9, 0.48], [0, 0.65, 0], p.light, 0.15);
  box(group, [1.3, 1.68, 0.045], [0, 0.65, 0.26], p.panel, 0.1);
  box(group, [0.9, 0.58, 0.025], [0, 0.94, 0.29], p.dark, 0.04);
  textLabel(group, "IAQ", [0, 0.94, 0.309], 0.53, accent);
  textLabel(group, "AIR QUALITY", [0, 0.48, 0.299], 0.7, p.frame);
  for (let i = 0; i < 7; i++)
    box(group, [0.75, 0.029, 0.035], [0, 0.04 + i * 0.044, 0.3], p.frame, 0.01);
  cylinder(group, 0.045, 0.014, [0, 1.38, 0.305], accent);
  const mount = box(group, [1.14, 1.5, 0.06], [0, 0.65, -0.29], p.frame, 0.05);
  return {
    group,
    setExploded(enabled) {
      mount.position.z = enabled ? -0.75 : -0.29;
    },
  };
}
