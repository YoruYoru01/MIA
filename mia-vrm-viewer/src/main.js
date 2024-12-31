import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { VRMLoaderPlugin, MToonMaterialLoaderPlugin } from '@pixiv/three-vrm';
import { MToonNodeMaterial } from '@pixiv/three-vrm/nodes';

document.addEventListener('DOMContentLoaded', () => {
    console.log('Iniciando visor VRM...');

    // Crear escena, cámara y renderizador
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });

    // Configurar renderizador
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);

    // Añadir luz a la escena
    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(0, 1, 2).normalize();
    scene.add(light);

    // Configurar posición de la cámara
    camera.position.z = 5;

    // Crear un cargador GLTF
    const loader = new GLTFLoader();

    // Registrar el VRMLoaderPlugin con soporte para WebGPU
    loader.register((parser) => {
        const mtoonMaterialPlugin = new MToonMaterialLoaderPlugin(parser, {
            materialType: MToonNodeMaterial, // Material compatible con WebGPU
        });

        return new VRMLoaderPlugin(parser, {
            mtoonMaterialPlugin,
        });
    });

    // Ruta del modelo VRM
    const vrmPath = './models/mia.vrm';

    // Cargar el modelo VRM
    loader.load(
        vrmPath,
        (gltf) => {
            const vrm = gltf.userData.vrm; // Obtener el modelo VRM cargado
            scene.add(vrm.scene); // Añadir modelo a la escena
            console.log('Modelo VRM cargado correctamente:', vrm);
        },
        (progress) => {
            console.log(`Cargando modelo: ${(progress.loaded / progress.total) * 100}% completado.`);
        },
        (error) => {
            console.error('Error al cargar el modelo VRM:', error);
        }
    );

    // Render Loop
    function animate() {
        requestAnimationFrame(animate);
        renderer.render(scene, camera);
    }
    animate();
});