/**
 * LiverWatch - 3D Interactive Liver Visualization
 * ================================================
 * 
 * Medically accurate 3D liver model showing disease progression
 * From healthy liver through various disease states.
 */

// Check if Three.js is loaded
function checkThreeJSLoaded() {
    if (typeof THREE === 'undefined') {
        console.warn('Three.js not loaded from CDN, loading alternative...');
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/three@0.128.0/build/three.min.js';
        script.onload = () => {
            console.log('Three.js loaded successfully');
            initializeLiverVisualization();
        };
        document.body.appendChild(script);
        return false;
    }
    return true;
}

function initializeLiverVisualization() {
    if (!checkThreeJSLoaded()) {
        return;
    }
    
    const liverViz = new LiverVisualization('liver-3d-container');
    
    // State selector buttons
    document.querySelectorAll('[data-liver-state]').forEach(button => {
        button.addEventListener('click', (e) => {
            const state = e.currentTarget.dataset.liverState;
            liverViz.changeState(state);
            
            // Update active button
            document.querySelectorAll('[data-liver-state]').forEach(btn => 
                btn.classList.remove('active')
            );
            e.currentTarget.classList.add('active');
        });
    });

    // Auto-play progression demo
    let autoPlayInterval;
    const autoPlayBtn = document.getElementById('auto-play-progression');
    if (autoPlayBtn) {
        autoPlayBtn.addEventListener('click', () => {
            const states = ['healthy', 'biliary_atresia', 'early_fibrosis', 'cirrhosis', 'liver_failure', 'liver_cancer'];
            let currentIndex = 0;
            
            if (autoPlayInterval) {
                clearInterval(autoPlayInterval);
                autoPlayInterval = null;
                autoPlayBtn.innerHTML = '<i class="fas fa-play"></i> Show Progression';
            } else {
                autoPlayBtn.innerHTML = '<i class="fas fa-pause"></i> Pause';
                autoPlayInterval = setInterval(() => {
                    currentIndex = (currentIndex + 1) % states.length;
                    liverViz.changeState(states[currentIndex]);
                    
                    // Update active button
                    document.querySelector(`[data-liver-state="${states[currentIndex]}"]`).click();
                }, 3000);
            }
        });
    }

    // Export to global scope
    window.liverVisualization = liverViz;
}

class LiverVisualization {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.liver = null;
        this.controls = null;
        this.currentState = 'healthy';
        this.animationId = null;

        // Disease state configurations
        this.diseaseStates = {
            healthy: {
                name: 'Healthy Liver',
                color: 0x8B2E2B, // Rich maroon
                roughness: 0.35,
                metalness: 0.15,
                bumpScale: 0.02,
                clearcoat: 0.3,
                transmission: 0.05,
                description: 'A healthy liver is smooth, firm, and reddish-brown. It efficiently filters blood, produces bile, and stores nutrients.',
                facts: [
                    'Weighs about 1.5 kg (3.3 lbs)',
                    'Processes over 500 vital functions',
                    'Regenerates damaged tissue naturally',
                    'Filters 1.4 liters of blood per minute'
                ]
            },
            biliary_atresia: {
                name: 'Biliary Atresia',
                color: 0x6B5B3A, // Olive/greenish brown
                roughness: 0.6,
                metalness: 0.05,
                bumpScale: 0.05,
                description: 'Bile ducts are blocked or absent. Bile accumulates, causing jaundice (yellowing). Without treatment within 60-90 days, permanent damage occurs.',
                facts: [
                    'Most common in infants (1 in 10,000 births)',
                    'Yellow/green discoloration from bile buildup',
                    'Kasai procedure must happen before 90 days',
                    'Early signs: persistent jaundice, pale stools, dark urine'
                ],
                progression: 'Stage 1: Early blockage',
                zones: [
                    { position: [0.3, 0.2, 0], severity: 0.4, label: 'Bile duct blockage' }
                ]
            },
            early_fibrosis: {
                name: 'Early Liver Scarring',
                color: 0x7A3B38, // Darker maroon
                roughness: 0.5,
                metalness: 0.08,
                bumpScale: 0.08,
                description: 'Early scar tissue (fibrosis) forms from repeated damage. Liver still functions but inflammation is present. Reversible with treatment.',
                facts: [
                    'Caused by hepatitis, alcohol, or fatty liver disease',
                    'Minimal symptoms - often undetected',
                    'Completely reversible at this stage',
                    'Regular monitoring crucial'
                ],
                progression: 'Stage 2: Scarring begins',
                zones: [
                    { position: [0.2, 0.1, 0.1], severity: 0.3, label: 'Early scarring' },
                    { position: [-0.2, 0.15, -0.1], severity: 0.2, label: 'Inflammation' }
                ]
            },
            cirrhosis: {
                name: 'Cirrhosis (Advanced Scarring)',
                color: 0x5A1916, // Very dark maroon/brown
                roughness: 0.7,
                metalness: 0.03,
                bumpScale: 0.15,
                description: 'Extensive scarring replaces healthy tissue. Liver surface becomes nodular and hard. Function significantly impaired but life can continue with management.',
                facts: [
                    'Affects 4-10% of Ugandans (Hep B related)',
                    'Surface becomes bumpy and hard',
                    'Can compensate for years with proper care',
                    'Portal hypertension causes complications'
                ],
                progression: 'Stage 3: Widespread damage',
                zones: [
                    { position: [0.3, 0.2, 0.1], severity: 0.7, label: 'Severe scarring' },
                    { position: [-0.3, 0.1, 0], severity: 0.8, label: 'Nodules forming' },
                    { position: [0.1, -0.2, 0.1], severity: 0.6, label: 'Blood flow restricted' },
                    { position: [-0.1, 0.25, -0.1], severity: 0.7, label: 'Portal hypertension' }
                ]
            },
            liver_failure: {
                name: 'Liver Failure (End Stage)',
                color: 0x3A1210, // Almost black-brown
                roughness: 0.9,
                metalness: 0.02,
                bumpScale: 0.25,
                description: 'Liver can no longer perform essential functions. Life-threatening emergency requiring immediate medical care and possible transplant evaluation.',
                facts: [
                    'Liver loses ability to filter toxins',
                    'Brain function affected (encephalopathy)',
                    'Bleeding risk increases dramatically',
                    'Transplant may be the only option'
                ],
                progression: 'Stage 4: Critical failure',
                zones: [
                    { position: [0.3, 0.1, 0], severity: 1.0, label: 'Complete failure' },
                    { position: [-0.3, 0.2, 0.1], severity: 1.0, label: 'No function' },
                    { position: [0, -0.2, 0], severity: 0.9, label: 'Severe atrophy' },
                    { position: [0.2, 0.3, -0.1], severity: 1.0, label: 'Necrosis' },
                    { position: [-0.2, -0.1, 0.1], severity: 0.95, label: 'Toxin buildup' }
                ]
            },
            liver_cancer: {
                name: 'Liver Cancer (Hepatocellular Carcinoma)',
                color: 0x2A0F0D, // Very dark with patches
                roughness: 0.8,
                metalness: 0.04,
                bumpScale: 0.3,
                description: 'Cancerous tumors develop, often in already damaged liver. Grows rapidly if untreated. Early detection is crucial for treatment options.',
                facts: [
                    'Often develops in cirrhotic livers',
                    'Visible as distinct nodules/masses',
                    '80% linked to chronic hepatitis B or C',
                    'Treatment includes surgery, ablation, or transplant'
                ],
                progression: 'Stage 5: Cancer development',
                zones: [
                    { position: [0.3, 0.2, 0], severity: 1.0, label: 'Primary tumor', size: 0.15 },
                    { position: [-0.2, 0.1, 0.1], severity: 0.8, label: 'Secondary growth', size: 0.08 },
                    { position: [0.1, -0.1, -0.1], severity: 0.9, label: 'Tumor invasion', size: 0.1 }
                ]
            },
            hepatitis_b: {
                name: 'Chronic Hepatitis B',
                color: 0x9A4039, // Inflamed reddish-brown
                roughness: 0.45,
                metalness: 0.09,
                bumpScale: 0.06,
                description: 'Viral infection causing chronic inflammation. Very common in Uganda (10-20% prevalence). Can lead to cirrhosis and cancer if untreated.',
                facts: [
                    '257 million people infected worldwide',
                    'Transmitted through blood and body fluids',
                    'Vaccine available - highly effective',
                    'Antiviral medications can control infection'
                ],
                progression: 'Chronic inflammation stage',
                zones: [
                    { position: [0.25, 0.15, 0.05], severity: 0.5, label: 'Viral activity' },
                    { position: [-0.2, 0.1, 0], severity: 0.45, label: 'Inflammation' },
                    { position: [0, 0.2, -0.1], severity: 0.4, label: 'Immune response' }
                ]
            },
            hepatitis_c: {
                name: 'Chronic Hepatitis C',
                color: 0x9B3D37, // Slightly different inflamed tone
                roughness: 0.47,
                metalness: 0.08,
                bumpScale: 0.07,
                description: 'Viral infection often causing silent damage for years. Major cause of cirrhosis worldwide. Curable with modern antiviral medications.',
                facts: [
                    '71 million people chronically infected',
                    'Often asymptomatic for decades',
                    '95% cure rate with direct-acting antivirals',
                    'No vaccine currently available'
                ],
                progression: 'Progressive inflammation',
                zones: [
                    { position: [0.2, 0.12, 0], severity: 0.55, label: 'Viral replication' },
                    { position: [-0.25, 0.15, 0.1], severity: 0.5, label: 'Hepatocyte damage' },
                    { position: [0.1, -0.1, 0], severity: 0.45, label: 'Fibrosis starting' }
                ]
            },
            fatty_liver: {
                name: 'Fatty Liver Disease (NAFLD)',
                color: 0xB8864B, // Yellowish-brown (fat accumulation)
                roughness: 0.55,
                metalness: 0.06,
                bumpScale: 0.04,
                description: 'Fat accumulates in liver cells (steatosis). Often linked to obesity, diabetes, and metabolic syndrome. Reversible with lifestyle changes.',
                facts: [
                    'Affects 25-30% of adults globally',
                    'Usually no symptoms in early stages',
                    'Weight loss of 10% can reverse it',
                    'Can progress to NASH (inflamed fatty liver)'
                ],
                progression: 'Fat accumulation stage',
                zones: [
                    { position: [0.3, 0.1, 0], severity: 0.35, label: 'Fat deposits' },
                    { position: [-0.3, 0.15, 0], severity: 0.3, label: 'Steatosis' },
                    { position: [0, 0.2, 0.1], severity: 0.25, label: 'Lipid accumulation' }
                ]
            },
            alcoholic_liver: {
                name: 'Alcoholic Liver Disease',
                color: 0x7D342A, // Damaged dark maroon
                roughness: 0.65,
                metalness: 0.05,
                bumpScale: 0.12,
                description: 'Chronic alcohol consumption damages liver cells and causes inflammation. Early stages (steatosis) are reversible with abstinence.',
                facts: [
                    'Develops after years of heavy drinking',
                    'Progresses: fatty liver → hepatitis → cirrhosis',
                    'Complete abstinence essential',
                    'Nutritional support aids recovery'
                ],
                progression: 'Alcohol-induced damage',
                zones: [
                    { position: [0.25, 0.15, 0], severity: 0.65, label: 'Hepatocyte death' },
                    { position: [-0.2, 0.1, 0.1], severity: 0.6, label: 'Inflammation' },
                    { position: [0.1, -0.15, 0], severity: 0.55, label: 'Early scarring' },
                    { position: [-0.1, 0.2, -0.1], severity: 0.5, label: 'Fat and fibrosis' }
                ]
            },
            hemochromatosis: {
                name: 'Hemochromatosis (Iron Overload)',
                color: 0x6B4423, // Brownish (iron deposits)
                roughness: 0.5,
                metalness: 0.25, // Higher metalness for iron
                bumpScale: 0.08,
                description: 'Genetic condition causing excessive iron absorption and storage. Iron deposits damage liver tissue. Treated with therapeutic phlebotomy.',
                facts: [
                    'Most common genetic disorder in Europeans',
                    'Liver stores excess iron',
                    'Can cause diabetes, heart problems',
                    'Regular blood removal removes iron'
                ],
                progression: 'Iron accumulation',
                zones: [
                    { position: [0.2, 0.1, 0], severity: 0.5, label: 'Iron deposits' },
                    { position: [-0.25, 0.15, 0], severity: 0.45, label: 'Hemosiderin' },
                    { position: [0.15, -0.1, 0.1], severity: 0.4, label: 'Oxidative damage' }
                ]
            },
            wilsons_disease: {
                name: "Wilson's Disease (Copper Overload)",
                color: 0x7A5C3E, // Copper-brownish
                roughness: 0.48,
                metalness: 0.22, // Copper metallic quality
                bumpScale: 0.09,
                description: 'Genetic disorder preventing copper excretion. Copper accumulates in liver and brain. Treatable with chelation therapy and zinc.',
                facts: [
                    'Affects 1 in 30,000 people',
                    'Usually appears in teens/young adults',
                    'Causes liver and neurological problems',
                    'Kayser-Fleischer rings in eyes (diagnostic)'
                ],
                progression: 'Copper toxicity',
                zones: [
                    { position: [0.2, 0.12, 0], severity: 0.55, label: 'Copper deposits' },
                    { position: [-0.2, 0.15, 0], severity: 0.5, label: 'Hepatocyte damage' },
                    { position: [0, 0.2, -0.1], severity: 0.45, label: 'Inflammation' }
                ]
            },
            autoimmune_hepatitis: {
                name: 'Autoimmune Hepatitis',
                color: 0x8A393F, // Inflamed reddish
                roughness: 0.52,
                metalness: 0.08,
                bumpScale: 0.1,
                description: 'Immune system attacks liver cells. More common in women. Causes chronic inflammation that can lead to cirrhosis if untreated.',
                facts: [
                    '70% of cases occur in women',
                    'Can occur at any age',
                    'Treated with immunosuppressants',
                    'Good prognosis with treatment'
                ],
                progression: 'Autoimmune inflammation',
                zones: [
                    { position: [0.25, 0.15, 0], severity: 0.6, label: 'Immune attack' },
                    { position: [-0.25, 0.1, 0.1], severity: 0.55, label: 'Interface hepatitis' },
                    { position: [0.1, -0.1, 0], severity: 0.5, label: 'Portal inflammation' },
                    { position: [-0.1, 0.2, -0.1], severity: 0.5, label: 'Hepatocyte necrosis' }
                ]
            },
            portal_hypertension: {
                name: 'Portal Hypertension',
                color: 0x6B2F2A, // Dark with vascular emphasis
                roughness: 0.62,
                metalness: 0.06,
                bumpScale: 0.13,
                description: 'Increased pressure in portal vein due to cirrhosis. Causes varices (enlarged veins), ascites, and splenomegaly. Serious complication.',
                facts: [
                    'Result of advanced cirrhosis',
                    'Causes life-threatening bleeding from varices',
                    'Leads to fluid accumulation (ascites)',
                    'May require TIPS procedure or shunt'
                ],
                progression: 'Vascular complication',
                zones: [
                    { position: [0, -0.2, 0], severity: 0.75, label: 'Portal vein pressure' },
                    { position: [0.3, 0.1, 0], severity: 0.7, label: 'Collateral vessels' },
                    { position: [-0.25, 0.15, 0], severity: 0.7, label: 'Venous congestion' },
                    { position: [0.1, 0.2, -0.1], severity: 0.65, label: 'Varices forming' }
                ]
            },
            liver_abscess: {
                name: 'Liver Abscess',
                color: 0x6D2F1F, // Dark with infection
                roughness: 0.75,
                metalness: 0.04,
                bumpScale: 0.18,
                description: 'Pus-filled cavity from bacterial, parasitic, or fungal infection. Causes fever, pain, and sepsis risk. Requires antibiotics and drainage.',
                facts: [
                    'Can be pyogenic (bacterial) or amoebic',
                    'Causes severe right-sided abdominal pain',
                    'High fever and sweating common',
                    'Treated with antibiotics ± drainage'
                ],
                progression: 'Infectious process',
                zones: [
                    { position: [0.3, 0.1, 0], severity: 0.85, label: 'Abscess cavity', size: 0.12 },
                    { position: [-0.2, 0.15, 0.1], severity: 0.7, label: 'Inflammation' },
                    { position: [0.1, 0.2, -0.1], severity: 0.65, label: 'Infected area' }
                ]
            }
        };

        this.init();
    }

    init() {
        // Scene setup
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xfdf2f2);
        this.scene.fog = new THREE.Fog(0xfdf2f2, 5, 15);

        // Camera
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        this.camera.position.set(3, 2, 4);

        // Renderer
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true, 
            alpha: true,
            powerPreference: 'high-performance'
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.container.appendChild(this.renderer.domElement);

        // Controls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 2;
        this.controls.maxDistance = 8;
        this.controls.maxPolarAngle = Math.PI / 1.5;

        // Lights
        this.setupLights();

        // Create liver model
        this.createLiver();

        // Add grid helper (subtle)
        const gridHelper = new THREE.GridHelper(5, 10, 0x8B2E2B, 0xfbd5d5);
        gridHelper.material.opacity = 0.1;
        gridHelper.material.transparent = true;
        this.scene.add(gridHelper);

        // Start animation
        this.animate();

        // Handle resize
        window.addEventListener('resize', () => this.onResize());
    }

    setupLights() {
        // Ambient light for base illumination
        const ambient = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambient);

        // Hemisphere light for natural lighting gradient
        const hemiLight = new THREE.HemisphereLight(0xffffff, 0x8B2E2B, 0.5);
        hemiLight.position.set(0, 20, 0);
        this.scene.add(hemiLight);

        // Main directional light (key light) - enhanced
        const mainLight = new THREE.DirectionalLight(0xffffff, 1.0);
        mainLight.position.set(5, 10, 5);
        mainLight.castShadow = true;
        mainLight.shadow.camera.near = 0.1;
        mainLight.shadow.camera.far = 50;
        mainLight.shadow.camera.left = -5;
        mainLight.shadow.camera.right = 5;
        mainLight.shadow.camera.top = 5;
        mainLight.shadow.camera.bottom = -5;
        mainLight.shadow.mapSize.width = 4096; // Increased for sharper shadows
        mainLight.shadow.mapSize.height = 4096;
        mainLight.shadow.bias = -0.0001;
        this.scene.add(mainLight);

        // Fill light (softer, warmer from side)
        const fillLight = new THREE.DirectionalLight(0xffe5e5, 0.6);
        fillLight.position.set(-5, 3, -5);
        this.scene.add(fillLight);

        // Rim light for depth and edge highlighting
        const rimLight = new THREE.DirectionalLight(0xffd5d5, 0.5);
        rimLight.position.set(0, -3, -5);
        this.scene.add(rimLight);

        // Additional point lights for subsurface scattering effect
        const pointLight1 = new THREE.PointLight(0xff6b6b, 0.4, 8);
        pointLight1.position.set(2, 1, 2);
        this.scene.add(pointLight1);

        const pointLight2 = new THREE.PointLight(0xffb3b3, 0.3, 8);
        pointLight2.position.set(-2, 1, -2);
        this.scene.add(pointLight2);

        // Subtle spotlight for depth
        const spotLight = new THREE.SpotLight(0xffffff, 0.3);
        spotLight.position.set(0, 8, 0);
        spotLight.angle = Math.PI / 4;
        spotLight.penumbra = 0.3;
        spotLight.castShadow = true;
        this.scene.add(spotLight);
    }

    createLiver() {
        // Create hyperrealistic anatomically-inspired liver shape
        const liverGroup = new THREE.Group();

        // Right lobe (larger, main part) - more anatomically accurate
        const rightLobeGeometry = new THREE.SphereGeometry(0.8, 128, 128); // Higher poly count
        rightLobeGeometry.scale(1.4, 0.85, 0.75);
        
        // Left lobe (smaller) - anatomically proportioned
        const leftLobeGeometry = new THREE.SphereGeometry(0.65, 128, 128);
        leftLobeGeometry.scale(1.1, 0.82, 0.68);
        leftLobeGeometry.translate(-0.75, 0.08, 0);

        // Caudate lobe (posterior, small)
        const caudateGeometry = new THREE.SphereGeometry(0.25, 64, 64);
        caudateGeometry.scale(0.9, 0.7, 0.6);
        caudateGeometry.translate(0.15, -0.2, -0.5);

        // Quadrate lobe (inferior surface)
        const quadrateGeometry = new THREE.SphereGeometry(0.22, 64, 64);
        quadrateGeometry.scale(0.8, 0.6, 0.7);
        quadrateGeometry.translate(0.1, -0.35, 0.25);

        // Merge all lobes for complete liver
        const mergedGeometry = this.mergeMultipleGeometries([
            rightLobeGeometry, 
            leftLobeGeometry,
            caudateGeometry,
            quadrateGeometry
        ]);
        
        // Add surface detail for organic appearance
        this.addSurfaceNoise(mergedGeometry);

        // Hyperrealistic material using Physical Material for better light interaction
        const state = this.diseaseStates.healthy;
        const liverMaterial = new THREE.MeshPhysicalMaterial({
            color: state.color,
            roughness: state.roughness || 0.35,
            metalness: state.metalness || 0.15,
            clearcoat: state.clearcoat || 0.3,
            clearcoatRoughness: 0.4,
            reflectivity: 0.6,
            envMapIntensity: 1.0,
            transparent: true,
            opacity: 0.98,
            side: THREE.FrontSide,
            // Simulate subsurface scattering for organic tissue
            transmission: state.transmission || 0.05,
            thickness: 0.8,
            ior: 1.4, // Index of refraction for biological tissue
            sheen: 0.2,
            sheenRoughness: 0.8,
            sheenColor: new THREE.Color(0xff9999)
        });

        this.liver = new THREE.Mesh(mergedGeometry, liverMaterial);
        this.liver.castShadow = true;
        this.liver.receiveShadow = true;
        this.liver.rotation.x = -0.15;
        this.liver.rotation.y = 0.1;
        
        liverGroup.add(this.liver);
        
        // Add anatomical blood vessels for realism
        this.addAnatomicalVessels(liverGroup);
        
        // Add ligaments/connective tissue
        this.addFalciformLigament(liverGroup);
        
        this.scene.add(liverGroup);
        this.liverGroup = liverGroup;

        // Store for disease markers
        this.diseaseMarkers = [];
    }

    mergeMultipleGeometries(geometries) {
        let totalVertices = 0;
        geometries.forEach(geo => {
            totalVertices += geo.getAttribute('position').count;
        });

        const positions = new Float32Array(totalVertices * 3);
        let offset = 0;

        geometries.forEach(geo => {
            const pos = geo.getAttribute('position');
            positions.set(pos.array, offset);
            offset += pos.count * 3;
        });

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.computeVertexNormals();
        
        return geometry;
    }

    addSurfaceNoise(geometry) {
        // Add organic surface irregularities
        const positions = geometry.attributes.position;
        const vertex = new THREE.Vector3();
        
        for (let i = 0; i < positions.count; i++) {
            vertex.fromBufferAttribute(positions, i);
            
            // Multi-octave noise for realistic organic surface
            const noise1 = Math.sin(vertex.x * 8 + vertex.y * 5) * 0.008;
            const noise2 = Math.cos(vertex.y * 12 + vertex.z * 7) * 0.006;
            const noise3 = Math.sin(vertex.z * 10 + vertex.x * 6) * 0.005;
            const combinedNoise = noise1 + noise2 + noise3;
            
            vertex.multiplyScalar(1 + combinedNoise);
            positions.setXYZ(i, vertex.x, vertex.y, vertex.z);
        }
        
        positions.needsUpdate = true;
        geometry.computeVertexNormals();
    }

    addAnatomicalVessels(group) {
        // Portal vein - large vessel entering liver
        const portalVeinMaterial = new THREE.MeshPhongMaterial({
            color: 0x6B1F1C,
            shininess: 60,
            transparent: true,
            opacity: 0.8
        });

        const portalVeinGeometry = new THREE.CylinderGeometry(0.12, 0.14, 2.5, 24);
        const portalVein = new THREE.Mesh(portalVeinGeometry, portalVeinMaterial);
        portalVein.position.set(0, -0.6, -0.15);
        portalVein.rotation.z = Math.PI / 8;
        portalVein.castShadow = true;
        group.add(portalVein);

        // Hepatic artery branches (redder, smaller)
        const arteryMaterial = new THREE.MeshPhongMaterial({
            color: 0xDC143C,
            shininess: 70,
            transparent: true,
            opacity: 0.75
        });

        // Create branching arterial structure
        const arteryPositions = [
            { pos: [0.3, 0.1, 0.2], rot: [0.5, 0.3, 0.2], scale: [0.07, 1.2] },
            { pos: [-0.35, 0.15, 0.1], rot: [-0.4, -0.2, 0.3], scale: [0.06, 1.0] },
            { pos: [0.15, -0.2, -0.1], rot: [0.3, 0.5, -0.2], scale: [0.05, 0.9] },
            { pos: [-0.2, -0.1, 0.2], rot: [-0.3, 0.4, 0.1], scale: [0.06, 1.1] },
            { pos: [0.25, 0.25, -0.15], rot: [0.2, -0.3, 0.4], scale: [0.05, 0.8] },
            { pos: [-0.15, 0.2, -0.2], rot: [-0.25, 0.35, -0.3], scale: [0.05, 0.85] }
        ];

        arteryPositions.forEach(data => {
            const branchGeo = new THREE.CylinderGeometry(data.scale[0], data.scale[0] * 0.7, data.scale[1], 16);
            const branch = new THREE.Mesh(branchGeo, arteryMaterial.clone());
            branch.position.set(...data.pos);
            branch.rotation.set(...data.rot);
            branch.castShadow = true;
            group.add(branch);
        });

        // Hepatic vein (draining blood out)
        const hepaticVeinMaterial = new THREE.MeshPhongMaterial({
            color: 0x8B0000,
            shininess: 55,
            transparent: true,
            opacity: 0.7
        });

        const hepaticVein = new THREE.Mesh(
            new THREE.CylinderGeometry(0.11, 0.11, 1.5, 20),
            hepaticVeinMaterial
        );
        hepaticVein.position.set(0.2, 0.5, -0.1);
        hepaticVein.rotation.set(0.3, 0, 0.2);
        hepaticVein.castShadow = true;
        group.add(hepaticVein);
    }

    addFalciformLigament(group) {
        // Falciform ligament - thin membrane attaching liver to abdominal wall
        const ligamentGeometry = new THREE.PlaneGeometry(0.3, 1.5, 8, 16);
        const ligamentMaterial = new THREE.MeshPhysicalMaterial({
            color: 0xffeaea,
            transparent: true,
            opacity: 0.3,
            side: THREE.DoubleSide,
            roughness: 0.7,
            transmission: 0.2
        });

        const ligament = new THREE.Mesh(ligamentGeometry, ligamentMaterial);
        ligament.position.set(0, 0.2, 0.3);
        ligament.rotation.y = Math.PI / 2;
        
        // Add slight wave to ligament
        const positions = ligament.geometry.attributes.position;
        for (let i = 0; i < positions.count; i++) {
            const y = positions.getY(i);
            const wave = Math.sin(y * 3) * 0.02;
            positions.setZ(i, positions.getZ(i) + wave);
        }
        positions.needsUpdate = true;
        
        group.add(ligament);
    }

    addAnatomicalDetails(group) {
        // Enhanced vascular details (kept for backwards compatibility)
        const vesselMaterial = new THREE.LineBasicMaterial({ 
            color: 0x6B1F1C, 
            opacity: 0.4, 
            transparent: true,
            linewidth: 2
        });

        // Surface vessel network
        const vesselPoints = [
            new THREE.Vector3(0, -0.5, 0),
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(0.3, 0.2, 0),
            new THREE.Vector3(-0.3, 0.1, 0)
        ];
        const vesselGeometry = new THREE.BufferGeometry().setFromPoints(vesselPoints);
        const vesselLine = new THREE.Line(vesselGeometry, vesselMaterial);
        group.add(vesselLine);
    }

    changeState(stateName) {
        if (!this.diseaseStates[stateName]) return;

        this.currentState = stateName;
        const state = this.diseaseStates[stateName];

        // Animate color transition
        this.animateMaterialChange(state);

        // Update UI
        this.updateInfoPanel(state);

        // Update disease markers
        this.updateDiseaseMarkers(state);
    }

    animateMaterialChange(state) {
        const startColor = new THREE.Color(this.liver.material.color);
        const endColor = new THREE.Color(state.color);
        const startRoughness = this.liver.material.roughness;
        const startMetalness = this.liver.material.metalness;

        const duration = 1500; // ms
        const startTime = Date.now();

        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Ease in-out
            const eased = progress < 0.5
                ? 2 * progress * progress
                : 1 - Math.pow(-2 * progress + 2, 2) / 2;

            // Interpolate color
            this.liver.material.color.lerpColors(startColor, endColor, eased);
            
            // Interpolate properties
            this.liver.material.roughness = startRoughness + (state.roughness - startRoughness) * eased;
            this.liver.material.metalness = startMetalness + (state.metalness - startMetalness) * eased;

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        animate();
    }

    updateDiseaseMarkers(state) {
        // Remove old markers
        this.diseaseMarkers.forEach(marker => {
            this.scene.remove(marker);
        });
        this.diseaseMarkers = [];

        // Add new markers if state has zones
        if (state.zones) {
            state.zones.forEach(zone => {
                const markerSize = zone.size || (0.05 + zone.severity * 0.1);
                const markerGeometry = new THREE.SphereGeometry(markerSize, 16, 16);
                
                // Color based on severity
                let markerColor;
                if (zone.severity < 0.3) markerColor = 0xfbbf24; // Yellow - mild
                else if (zone.severity < 0.7) markerColor = 0xf59e0b; // Orange - moderate
                else markerColor = 0xef4444; // Red - severe

                const markerMaterial = new THREE.MeshStandardMaterial({
                    color: markerColor,
                    emissive: markerColor,
                    emissiveIntensity: 0.3,
                    roughness: 0.4,
                    metalness: 0.2
                });

                const marker = new THREE.Mesh(markerGeometry, markerMaterial);
                marker.position.set(zone.position[0], zone.position[1], zone.position[2]);
                
                // Pulsing animation
                marker.userData.initialScale = markerSize;
                marker.userData.pulseSpeed = 1 + Math.random();
                
                this.liverGroup.add(marker);
                this.diseaseMarkers.push(marker);
            });
        }
    }

    updateInfoPanel(state) {
        // Update text content
        document.getElementById('liver-state-name').textContent = state.name;
        document.getElementById('liver-state-description').textContent = state.description;
        
        // Update facts list
        const factsList = document.getElementById('liver-facts-list');
        factsList.innerHTML = state.facts.map(fact => 
            `<li><i class="fas fa-check-circle"></i> ${fact}</li>`
        ).join('');

        // Update progression stage if exists
        const progressionEl = document.getElementById('liver-progression');
        if (state.progression) {
            progressionEl.textContent = state.progression;
            progressionEl.style.display = 'block';
        } else {
            progressionEl.style.display = 'none';
        }

        // Update severity indicator
        this.updateSeverityIndicator(state);
    }

    updateSeverityIndicator(state) {
        const severityBar = document.getElementById('severity-bar');
        const severityLabel = document.getElementById('severity-label');
        
        let severity = 0;
        let label = 'Healthy';
        let color = '#10b981';

        const severityMap = {
            'healthy': { severity: 0, label: 'Healthy', color: '#10b981' },
            'biliary_atresia': { severity: 40, label: 'Early Damage', color: '#fbbf24' },
            'early_fibrosis': { severity: 35, label: 'Reversible', color: '#f59e0b' },
            'fatty_liver': { severity: 30, label: 'Fatty Deposits', color: '#f59e0b' },
            'hepatitis_b': { severity: 50, label: 'Chronic Inflammation', color: '#fb923c' },
            'hepatitis_c': { severity: 52, label: 'Progressive', color: '#fb923c' },
            'autoimmune_hepatitis': { severity: 55, label: 'Autoimmune', color: '#fb923c' },
            'hemochromatosis': { severity: 48, label: 'Iron Overload', color: '#f59e0b' },
            'wilsons_disease': { severity: 50, label: 'Copper Toxicity', color: '#f59e0b' },
            'alcoholic_liver': { severity: 60, label: 'Alcohol Damage', color: '#f97316' },
            'cirrhosis': { severity: 70, label: 'Advanced', color: '#f97316' },
            'portal_hypertension': { severity: 75, label: 'Vascular Crisis', color: '#ef4444' },
            'liver_abscess': { severity: 80, label: 'Infection', color: '#ef4444' },
            'liver_failure': { severity: 95, label: 'Critical', color: '#ef4444' },
            'liver_cancer': { severity: 90, label: 'Cancer', color: '#dc2626' }
        };

        const data = severityMap[this.currentState] || severityMap['healthy'];
        severity = data.severity;
        label = data.label;
        color = data.color;

        severityBar.style.width = severity + '%';
        severityBar.style.backgroundColor = color;
        severityLabel.textContent = label;
    }

    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());

        // Gentle rotation
        if (this.liverGroup) {
            this.liverGroup.rotation.y += 0.002;
        }

        // Pulse disease markers
        this.diseaseMarkers.forEach((marker, index) => {
            const time = Date.now() * 0.001;
            const pulse = Math.sin(time * marker.userData.pulseSpeed) * 0.1 + 1;
            marker.scale.setScalar(pulse);
        });

        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    onResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    dispose() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        this.renderer.dispose();
        this.controls.dispose();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeLiverVisualization);
