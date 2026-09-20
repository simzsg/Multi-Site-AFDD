import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { createAhuModel } from "./models/AhuModel";
import { createIaqModel } from "./models/IaqModel";
import { createMeterModel } from "./models/MeterModel";
import type { Entity, Observation } from "../../types";
import { SceneFallback, SceneReadings } from "./EquipmentSceneOverlay";
export type CameraView = "isometric" | "front" | "top";
export type SceneProps = {
  points: Entity[];
  current: Record<string, Observation>;
  onSelectPoint: (point: Entity) => void;
  kind: string;
  equipmentName: string;
  activeFault: boolean;
  running: boolean;
  exploded: boolean;
  rotate: boolean;
  cameraView: CameraView;
  resetKey: number;
};

export default function EquipmentScene(props: SceneProps) {
  const overlay = useRef<HTMLDivElement>(null);
  const host = useRef<HTMLDivElement>(null);
  const settings = useRef(props);
  settings.current = props;
  const api = useRef<{
    refresh: () => void;
    setCamera: (view: CameraView) => void;
  } | null>(null);
  const [failed, setFailed] = useState(false);
  const [ready, setReady] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const container = host.current;
    if (!container) return;
    let renderer: THREE.WebGLRenderer;
    setFailed(false);
    setReady(false);
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "low-power",
      });
    } catch {
      setFailed(true);
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.5;
    renderer.domElement.setAttribute(
      "aria-label",
      `${props.equipmentName}: interactive illustrative 3D model. Drag to orbit, scroll to zoom. Arrow keys rotate; Home resets.`,
    );
    renderer.domElement.setAttribute("role", "img");
    renderer.domElement.tabIndex = 0;
    renderer.domElement.style.touchAction = "pan-y";
    container.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 60);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = false;
    controls.minDistance = 4.2;
    controls.maxDistance = 12;
    controls.maxPolarAngle = Math.PI * 0.48;
    controls.autoRotateSpeed = 0.5;
    controls.touches.ONE = THREE.TOUCH.ROTATE;
    controls.touches.TWO = THREE.TOUCH.DOLLY_PAN;
    const ambient = new THREE.HemisphereLight("#ffffff", "#728279", 2.1);
    scene.add(ambient);
    const key = new THREE.DirectionalLight("#fff5dc", 4);
    key.position.set(-3, 7, 5);
    key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024);
    key.shadow.camera.left = -4;
    key.shadow.camera.right = 4;
    key.shadow.camera.top = 4;
    key.shadow.camera.bottom = -4;
    key.shadow.normalBias = 0.035;
    scene.add(key);
    const fill = new THREE.DirectionalLight("#bfdfd0", 2);
    fill.position.set(4, 3, -4);
    scene.add(fill);
    const model = (
      props.kind === "IAQ_Device"
        ? createIaqModel
        : props.kind === "Electrical_Meter"
          ? createMeterModel
          : createAhuModel
    )(props.activeFault ? "#e3ac70" : "#96cfa7");
    scene.add(model.group);
    const platform = new THREE.Mesh(
      new THREE.CylinderGeometry(3.05, 3.12, 0.14, 96),
      new THREE.MeshStandardMaterial({ color: "#d8e1d6", roughness: 0.9 }),
    );
    platform.position.y = -0.14;
    platform.receiveShadow = true;
    scene.add(platform);
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(80, 80),
      new THREE.ShadowMaterial({ opacity: 0.13 }),
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.215;
    floor.receiveShadow = true;
    scene.add(floor);
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(2.75, 2.76, 96),
      new THREE.MeshBasicMaterial({ color: "#9bae9d", side: THREE.DoubleSide }),
    );
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = -0.063;
    scene.add(ring);
    let frame = 0,
      visible = true,
      inViewport = true,
      disposed = false,
      last = performance.now();
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    const requestRender = () => {
      if (!frame && visible && !disposed) frame = requestAnimationFrame(render);
    };
    function render(now: number) {
      frame = 0;
      if (disposed || !visible) return;
      const state = settings.current;
      model.setExploded(state.exploded);
      controls.autoRotate = state.rotate && !reduced.matches;
      if (model.fan && state.running && !reduced.matches)
        model.fan.rotation.z -= Math.min((now - last) / 1000, 0.05) * 2;
      last = now;
      controls.update();
      renderer.render(scene, camera);
      const w = container!.clientWidth,
        h = container!.clientHeight;
      overlay.current
        ?.querySelectorAll<HTMLElement>("[data-anchor]")
        .forEach((element) => {
          const anchor = JSON.parse(element.dataset.anchor!) as [
            number,
            number,
            number,
          ];
          const projected = new THREE.Vector3(...anchor).project(camera);
          const x = ((projected.x + 1) * w) / 2,
            y = ((1 - projected.y) * h) / 2;
          const index = Number(element.dataset.index);
          const left = index % 2 === 0;
          const labelX = left ? 8 : w - 128;
          const labelY = index < 2 ? 80 : h - 115;
          element.style.transform = `translate(${labelX}px, ${labelY}px)`;
          const line = overlay.current?.querySelector<SVGLineElement>(
            `[data-line="${index}"]`,
          );
          line?.setAttribute("x1", String(left ? labelX + 120 : labelX));
          line?.setAttribute("y1", String(labelY + 30));
          line?.setAttribute("x2", String(x));
          line?.setAttribute("y2", String(y));
        });
      if (
        controls.autoRotate ||
        (model.fan && state.running && !reduced.matches)
      )
        requestRender();
    }
    function setCamera(view: CameraView) {
      controls.target.set(0, props.kind === "AHU" ? 1.0 : 1.05, 0);
      camera.position.set(
        ...((view === "front"
          ? [0, 1.5, 8.8]
          : view === "top"
            ? [0.01, 9, 0.1]
            : [5.6, 4.1, 6.7]) as [number, number, number]),
      );
      controls.update();
      requestRender();
    }
    const resize = new ResizeObserver(() => {
      const w = container.clientWidth,
        h = container.clientHeight;
      if (!w || !h) return;
      camera.aspect = w / h;
      camera.fov = THREE.MathUtils.radToDeg(
        2 *
          Math.atan(
            Math.tan(THREE.MathUtils.degToRad(34) / 2) *
              Math.max(1, 1.6 / camera.aspect),
          ),
      );
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      requestRender();
    });
    resize.observe(container);
    const observer = new IntersectionObserver(
      ([entry]) => {
        inViewport = entry.isIntersecting;
        visible = inViewport && !document.hidden;
        if (visible) requestRender();
        else {
          cancelAnimationFrame(frame);
          frame = 0;
        }
      },
      { threshold: 0.01 },
    );
    observer.observe(container);
    const visibility = () => {
      visible = inViewport && !document.hidden;
      if (visible) requestRender();
    };
    document.addEventListener("visibilitychange", visibility);
    const keydown = (event: KeyboardEvent) => {
      if (
        !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home"].includes(
          event.key,
        )
      )
        return;
      event.preventDefault();
      if (event.key === "Home") {
        setCamera("isometric");
        return;
      }
      const offset = camera.position.clone().sub(controls.target);
      const spherical = new THREE.Spherical().setFromVector3(offset);
      if (event.key === "ArrowLeft") spherical.theta -= 0.16;
      if (event.key === "ArrowRight") spherical.theta += 0.16;
      if (event.key === "ArrowUp")
        spherical.phi = Math.max(0.05, spherical.phi - 0.12);
      if (event.key === "ArrowDown")
        spherical.phi = Math.min(Math.PI * 0.48, spherical.phi + 0.12);
      camera.position
        .copy(controls.target)
        .add(new THREE.Vector3().setFromSpherical(spherical));
      controls.update();
      requestRender();
    };
    renderer.domElement.addEventListener("keydown", keydown);
    const lost = (event: Event) => {
      event.preventDefault();
      setFailed(true);
      visible = false;
      cancelAnimationFrame(frame);
      frame = 0;
    };
    renderer.domElement.addEventListener("webglcontextlost", lost);
    controls.addEventListener("change", requestRender);
    reduced.addEventListener("change", requestRender);
    api.current = { refresh: requestRender, setCamera };
    setCamera(settings.current.cameraView);
    setReady(true);
    return () => {
      disposed = true;
      api.current = null;
      cancelAnimationFrame(frame);
      resize.disconnect();
      observer.disconnect();
      document.removeEventListener("visibilitychange", visibility);
      reduced.removeEventListener("change", requestRender);
      renderer.domElement.removeEventListener("keydown", keydown);
      renderer.domElement.removeEventListener("webglcontextlost", lost);
      controls.removeEventListener("change", requestRender);
      controls.dispose();
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh) {
          object.geometry.dispose();
          const materials = Array.isArray(object.material)
            ? object.material
            : [object.material];
          materials.forEach((mat) => {
            if ("map" in mat && mat.map instanceof THREE.Texture)
              mat.map.dispose();
            mat.dispose();
          });
        }
      });
      renderer.dispose();
      renderer.forceContextLoss();
      renderer.domElement.remove();
    };
  }, [props.kind, props.activeFault, retry]);
  useEffect(() => {
    api.current?.refresh();
  }, [
    props.running,
    props.exploded,
    props.rotate,
    props.points,
    props.current,
    ready,
  ]);
  useEffect(() => {
    api.current?.setCamera(props.cameraView);
  }, [props.cameraView, props.resetKey]);
  useEffect(() => {
    const canvas = host.current?.querySelector("canvas");
    canvas?.setAttribute(
      "aria-label",
      `${props.equipmentName}: interactive illustrative 3D model. Drag to orbit, scroll to zoom. Arrow keys rotate; Home resets.`,
    );
  }, [props.equipmentName]);
  return (
    <div
      className="relative h-full w-full"
      data-testid="equipment-scene"
      data-scene-state={failed ? "fallback" : ready ? "ready" : "loading"}
    >
      <div ref={host} className="h-full w-full" />
      {!failed && ready && (
        <SceneReadings
          points={props.points}
          current={props.current}
          onSelectPoint={props.onSelectPoint}
          overlayRef={overlay}
        />
      )}
      {failed && <SceneFallback onRetry={() => setRetry((value) => value + 1)} />}
    </div>
  );
}
