import * as THREE from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";

export const palette = {
  frame: "#284f48",
  panel: "#c9dcd0",
  light: "#e8eee4",
  dark: "#213e39",
  copper: "#c69567",
  accent: "#96cfa7",
};
export function material(color: string, metalness = 0.15, roughness = 0.55) {
  return new THREE.MeshStandardMaterial({ color, metalness, roughness });
}
export function box(
  parent: THREE.Object3D,
  size: [number, number, number],
  position: [number, number, number],
  color: string,
  radius = 0.025,
) {
  const mesh = new THREE.Mesh(
    radius
      ? new RoundedBoxGeometry(
          ...size,
          2,
          Math.min(radius, Math.min(...size) / 3),
        )
      : new THREE.BoxGeometry(...size),
    material(color),
  );
  mesh.position.set(...position);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  parent.add(mesh);
  return mesh;
}
export function cylinder(
  parent: THREE.Object3D,
  radius: number,
  depth: number,
  position: [number, number, number],
  color: string,
) {
  const mesh = new THREE.Mesh(
    new THREE.CylinderGeometry(radius, radius, depth, 32),
    material(color, 0.45, 0.35),
  );
  mesh.rotation.x = Math.PI / 2;
  mesh.position.set(...position);
  mesh.castShadow = true;
  parent.add(mesh);
  return mesh;
}
export function textLabel(
  parent: THREE.Object3D,
  text: string,
  position: [number, number, number],
  width = 0.75,
  color = "#e8eee4",
) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 128;
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = color;
  ctx.font = "600 48px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, 256, 64);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const mesh = new THREE.Mesh(
    new THREE.PlaneGeometry(width, width / 4),
    new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      depthWrite: false,
    }),
  );
  mesh.position.set(...position);
  parent.add(mesh);
  return mesh;
}
export type EquipmentModel = {
  group: THREE.Group;
  fan?: THREE.Group;
  setExploded: (enabled: boolean) => void;
};
