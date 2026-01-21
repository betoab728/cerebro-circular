<script lang="ts">
  import Navbar from '$lib/components/Navbar.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import { API_BASE_URL } from '$lib/config';
  import { fade, slide } from 'svelte/transition';

  // --- ANALYSIS STATE ---
  let isAnalyzing = $state(false);
  let analysisResult = $state(null);
  let showModal = $state(false);
  let currentUploadType = $state('');
  let file: File | null = $state(null);
  let dragging = $state(false);

  // --- FORM STATE ---
  let formData = $state({
    razon_social: '',
    planta: '',
    departamento: '',
    responsable: '',
    unidad_generadora: '',
    tipo_residuo: '',
    codigo_basilea: '',
    caracteristica: '',
    cantidad: null,
    unidad_medida: '',
    volumen: null,
    peso_total: null,
    frecuencia: ''
  });

  let isSaving = $state(false);
  let successMessage = $state('');
  let errorMessage = $state('');

  const uploadOptions = [
    { 
      id: 'technical', title: 'Ficha Técnica', desc: 'PDF de especificaciones', 
      icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      color: 'bg-blue-50 text-blue-600', accept: '.pdf'
    },
    { 
      id: 'security', title: 'Hoja de Seguridad', desc: 'MSDS / HDS', 
      icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
      color: 'bg-amber-50 text-amber-600', accept: '.pdf'
    },
    { 
      id: 'photo', title: 'Fotografía', desc: 'Visión por IA', 
      icon: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z',
      color: 'bg-purple-50 text-purple-600', accept: 'image/*'
    }
  ];

  const unidadesGeneradoras = ['ADMINISTRACION', 'OPERACIONES', 'MANTENIMIENTO', 'MAESTRANZA', 'TOPICO', 'ALMACEN1', 'ALMACEN2', 'POLVORIN', 'COMEDOR', 'OTROS'];
  const tiposResiduo = ['PELIGROSO', 'NO PELIGROSO', 'NFU', 'RAEE', 'ESPECIAL', 'OTROS'];
  const unidadesMedida = ['KILOGRAMO', 'METROS CUBICOS', 'OTROS'];

  // --- ACTIONS ---

  function openUpload(typeId: string) {
    currentUploadType = typeId;
    file = null;
    showModal = true;
  }

  async function startAnalysis() {
    if (!file) return;
    isAnalyzing = true;
    analysisResult = null;
    errorMessage = '';

    try {
      const data = new FormData();
      data.append('file', file);
      data.append('type', currentUploadType);
      
      // Send current form data as context for better AI analysis
      data.append('context', JSON.stringify(formData));

      const response = await fetch(`${API_BASE_URL}/analyze`, { method: 'POST', body: data });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown Error' }));
        throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
      }

      analysisResult = await response.json();
      
      // Auto-fill some form data from AI
      formData.tipo_residuo = analysisResult.category === 'Peligroso' ? 'PELIGROSO' : 'NO PELIGROSO';
      formData.caracteristica = analysisResult.materialName;
      formData.codigo_basilea = analysisResult.baselCode || '';
      
    } catch (err) {
      errorMessage = `Error de Análisis: ${err.message}`;
    } finally {
      isAnalyzing = false;
    }
  }

  async function handleRegister() {
    isSaving = true;
    errorMessage = '';
    successMessage = '';

    try {
      const payload = {
        ...formData,
        // Analysis Data
        analysis_material_name: analysisResult?.materialName,
        analysis_physicochemical: JSON.stringify(analysisResult?.physicochemical),
        analysis_elemental: JSON.stringify(analysisResult?.elemental),
        analysis_engineering: JSON.stringify(analysisResult?.engineeringContext),
        analysis_valorization: JSON.stringify(analysisResult?.valorizationRoutes),
        
        // New Summarized Fields
        oportunidades_ec: analysisResult?.valorizationRoutes?.[0]?.output || 'No especificado',
        viabilidad_ec: analysisResult?.valorizationRoutes?.[0]?.score || 0,

        // Financials (Now hidden/zeroed)
        costo_disposicion_final: 0,
        ingreso_economia_circular: 0
      };

      const response = await fetch(`${API_BASE_URL}/waste/generation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('Error al guardar el registro');

      successMessage = 'Registro Inteligente guardado con éxito';
      // Reset form (optional, could also redirect)
      analysisResult = null;
    } catch (err) {
      errorMessage = err.message;
    } finally {
      isSaving = false;
    }
  }

  function handleFileSelect(e: any) {
    const input = e.target;
    if (input.files?.[0]) {
      file = input.files[0];
      showModal = false;
      startAnalysis();
    }
  }
</script>

<Navbar title="Registro Inteligente & Caracterización" />

<div class="p-6 md:p-10 max-w-3xl mx-auto space-y-10 pb-24">
  
  <header class="text-center space-y-2">
    <h1 class="text-3xl font-extrabold text-gray-900 tracking-tight">Registro Inteligente con IA</h1>
    <p class="text-gray-500">Ingresa los datos operativos y deja que nuestra IA caracterice técnicamente el residuo.</p>
  </header>

  {#if successMessage}
    <div transition:fade class="p-5 bg-green-50 text-green-700 rounded-2xl border border-green-100 flex items-center justify-between shadow-sm">
      <div class="flex items-center gap-3">
        <div class="bg-green-100 p-2 rounded-full"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg></div>
        <span class="font-medium">{successMessage}</span>
      </div>
      <a href="/registry" class="text-sm font-bold underline hover:text-green-800">Ver Historial</a>
    </div>
  {/if}

  {#if errorMessage}
    <div transition:fade class="p-5 bg-red-50 text-red-700 rounded-2xl border border-red-100 flex items-center gap-3 shadow-sm">
      <div class="bg-red-100 p-2 rounded-full"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg></div>
      <span class="font-medium">{errorMessage}</span>
    </div>
  {/if}

  <div class="space-y-8">
    
    <!-- STEP 1: Basic & Scale Data -->
    <section class="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 space-y-6">
       <div class="flex items-center gap-3 mb-2">
         <div class="w-8 h-8 bg-scientific-600 text-white rounded-full flex items-center justify-center font-bold">1</div>
         <h2 class="text-xl font-bold text-gray-800">Datos de Generación y Escala</h2>
       </div>

       <!-- ORG INFO -->
       <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
         <div class="space-y-1.5 focus-within:text-scientific-600 transition-colors">
           <label class="block text-xs font-bold uppercase tracking-wider text-gray-400">Razón Social</label>
           <input type="text" bind:value={formData.razon_social} class="w-full h-12 rounded-xl border-gray-200 focus:ring-4 focus:ring-scientific-50/50 focus:border-scientific-400 transition-all px-4" placeholder="Empresa S.A." />
         </div>
         <div class="space-y-1.5">
           <label class="block text-xs font-bold uppercase tracking-wider text-gray-400">Planta</label>
           <input type="text" bind:value={formData.planta} class="w-full h-12 rounded-xl border-gray-200 focus:ring-4 focus:ring-scientific-50/50 focus:border-scientific-400 transition-all px-4" placeholder="Planta Principal" />
         </div>
         <div class="space-y-1.5">
           <label class="block text-xs font-bold uppercase tracking-wider text-gray-400">Departamento</label>
           <input type="text" bind:value={formData.departamento} class="w-full h-12 rounded-xl border-gray-200 focus:ring-4 focus:ring-scientific-50/50 focus:border-scientific-400 transition-all px-4" placeholder="Logística" />
         </div>
       </div>

       <div class="grid grid-cols-1 md:grid-cols-4 gap-6 pt-2">
         <div class="space-y-1.5 focus-within:text-scientific-600 transition-colors">
           <label class="block text-xs font-bold uppercase tracking-wider text-gray-400">Responsable</label>
           <input type="text" required bind:value={formData.responsable} class="w-full h-12 rounded-xl border-gray-200 focus:ring-4 focus:ring-scientific-50/50 focus:border-scientific-400 transition-all px-4" placeholder="Nombre completo" />
         </div>
         <div class="space-y-1.5">
           <label class="block text-xs font-bold uppercase tracking-wider text-gray-400">Unidad Generadora</label>
           <select required bind:value={formData.unidad_generadora} class="w-full h-12 rounded-xl border-gray-200 focus:ring-4 focus:ring-scientific-50/50 focus:border-scientific-400 transition-all px-4 bg-white">
             <option value="" disabled>Seleccione unidad...</option>
             {#each unidadesGeneradoras as u} <option value={u}>{u}</option> {/each}
           </select>
         </div>
         <div class="space-y-1.5">
           <label class="block text-xs font-bold uppercase tracking-wider text-gray-400">Tipo de Residuo</label>
           <select required bind:value={formData.tipo_residuo} class="w-full h-12 rounded-xl border-gray-200 focus:ring-4 focus:ring-scientific-50/50 focus:border-scientific-400 transition-all px-4 bg-white">
             <option value="" disabled>Seleccione...</option>
             {#each tiposResiduo as t} <option value={t}>{t}</option> {/each}
           </select>
         </div>
         <div class="space-y-1.5">
            <label class="block text-xs font-bold uppercase tracking-wider text-gray-400">Código de Basilea</label>
            <input type="text" bind:value={formData.codigo_basilea} class="w-full h-12 rounded-xl border-gray-200 focus:ring-4 focus:ring-scientific-50/50 focus:border-scientific-400 transition-all px-4" placeholder="Ej: A1180" />
         </div>
       </div>

       <div class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
         <div class="space-y-1.5">
           <label class="block text-xs font-bold uppercase tracking-wider text-gray-400">Cantidad</label>
           <input type="number" step="0.01" required bind:value={formData.cantidad} class="w-full h-12 rounded-xl border-gray-200 focus:ring-4 focus:border-scientific-400 px-4" placeholder="0.00" />
         </div>
         <div class="space-y-1.5">
           <label class="block text-xs font-bold uppercase tracking-wider text-gray-400">Unidad Medida</label>
           <select required bind:value={formData.unidad_medida} class="w-full h-12 rounded-xl border-gray-200 focus:border-scientific-400 px-4 bg-white">
             {#each unidadesMedida as um} <option value={um}>{um}</option> {/each}
           </select>
         </div>
         <div class="space-y-1.5">
           <label class="block text-xs font-bold uppercase tracking-wider text-gray-400">Peso Total (kg)</label>
           <input type="number" step="0.01" required bind:value={formData.peso_total} class="w-full h-12 rounded-xl border-gray-200 border-2 border-scientific-100 focus:border-scientific-400 px-4 font-bold text-scientific-700" placeholder="0.00 kg" />
         </div>
       </div>

       <div class="space-y-1.5 pt-2">
          <label class="block text-xs font-bold uppercase tracking-wider text-gray-400">Descripción Inicial</label>
          <textarea bind:value={formData.caracteristica} rows="2" class="w-full rounded-xl border-gray-200 focus:border-scientific-400 px-4 py-3" placeholder="Ej: Plástico de envase de suero, cartón corrugado empapado..."></textarea>
       </div>
    </section>

    <!-- STEP 2: AI Characterization -->
    <section class="bg-gradient-to-br from-scientific-50/50 to-white p-8 rounded-2xl shadow-sm border border-scientific-100 space-y-6">
       <div class="flex items-center gap-3 mb-2">
         <div class="w-8 h-8 bg-scientific-600 text-white rounded-full flex items-center justify-center font-bold">2</div>
         <h2 class="text-xl font-bold text-gray-800">Caracterización Técnica con IA</h2>
       </div>

       {#if !analysisResult && !isAnalyzing}
         <div in:fade class="grid grid-cols-1 sm:grid-cols-3 gap-4">
           {#each uploadOptions as opt}
             <button on:click={() => openUpload(opt.id)} class="flex flex-col items-center p-6 bg-white border border-gray-100 rounded-2xl hover:border-scientific-400 hover:shadow-md transition-all group scale-100 hover:scale-[1.02] active:scale-95">
               <div class={`w-14 h-14 rounded-2xl flex items-center justify-center mb-4 ${opt.color} group-hover:scale-110 transition-transform`}>
                  <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={opt.icon} /></svg>
               </div>
               <span class="text-sm font-bold text-gray-700">{opt.title}</span>
               <span class="text-[10px] text-gray-400 mt-1 uppercase tracking-tighter">{opt.desc}</span>
             </button>
           {/each}
         </div>
       {:else if isAnalyzing}
         <div in:fade class="py-12 flex flex-col items-center justify-center text-center space-y-5 bg-white rounded-2xl border border-dashed border-scientific-200">
           <svg class="animate-spin h-12 w-12 text-scientific-600" viewBox="0 0 24 24">
             <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
             <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
           </svg>
           <div class="space-y-1">
              <p class="text-scientific-700 font-bold text-lg">Cross-referencing scale data...</p>
              <p class="text-xs text-gray-400 uppercase tracking-widest">Escalando análisis a {formData.peso_total || 0} kg</p>
           </div>
         </div>
       {:else if analysisResult}
         <div in:slide class="space-y-6">
           <!-- AI RESULTS BANNER -->
           <div class="bg-white p-6 rounded-2xl border border-scientific-200 shadow-sm relative overflow-hidden">
              <div class="absolute top-0 right-0 p-3"><button on:click={() => { analysisResult = null; file = null; }} class="text-red-500 hover:text-red-700 transition-colors"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg></button></div>
              <div class="flex flex-col md:flex-row gap-6 items-start">
                 <div class="flex-1 space-y-1">
                    <span class="text-[10px] font-bold uppercase tracking-widest text-scientific-600">Material Detectado</span>
                    <h3 class="text-2xl font-black text-gray-900 leading-none">{analysisResult.materialName}</h3>
                    <div class="flex gap-2 pt-1">
                       <span class="px-2 py-0.5 bg-gray-100 rounded text-[10px] font-bold text-gray-500 uppercase tracking-tighter">Confianza: {analysisResult.confidence}%</span>
                       <span class="px-2 py-0.5 bg-scientific-50 rounded text-[10px] font-bold text-scientific-700 uppercase tracking-tighter">Cat: {analysisResult.category}</span>
                    </div>
                 </div>
                 
                  <div class="w-full md:w-auto grid grid-cols-1 gap-3">
                     <div class="bg-scientific-600 p-4 rounded-xl text-white text-center min-w-[200px]">
                        <span class="block text-[10px] font-bold uppercase opacity-80 mb-1">Métrica de Procesabilidad</span>
                        <p class="text-xs leading-tight font-medium">{analysisResult.engineeringContext.processability}</p>
                     </div>
                  </div>
              </div>

              <!-- VALORIZATION ROUTES (Integrated) -->
              <div class="mt-8 space-y-3">
                <h4 class="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
                   <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                   Oportunidades de Economía Circular
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                   {#each analysisResult.valorizationRoutes as route}
                     <div class="p-4 rounded-xl border-2 {route.score >= 90 ? 'border-green-50 bg-green-50/20' : 'border-gray-50 bg-gray-50/30'} flex justify-between items-center group hover:border-scientific-200 transition-all">
                        <div class="max-w-[70%]">
                           <p class="text-[10px] font-black text-gray-400 uppercase leading-none mb-1">{route.method}</p>
                           <p class="text-sm font-bold text-gray-800 leading-tight">{route.output}</p>
                        </div>
                        <div class="text-right">
                           <span class="block text-lg font-black {route.score >= 90 ? 'text-green-600' : 'text-gray-400'}">{route.score}%</span>
                           <span class="text-[9px] font-bold text-gray-400 uppercase">Viabilidad</span>
                        </div>
                     </div>
                   {/each}
                </div>
              </div>
           </div>
         </div>
       {/if}
    </section>

    <!-- STEP 3: Final Registration -->
    <section class="space-y-4">
       <button 
         on:click={handleRegister}
         disabled={isSaving || isAnalyzing}
         class="w-full h-16 bg-scientific-600 hover:bg-scientific-700 text-white font-black text-lg rounded-2xl shadow-xl shadow-scientific-200 transition-all flex items-center justify-center gap-4 group disabled:opacity-50"
       >
         {#if isSaving}
            <svg class="animate-spin h-6 w-6 text-white" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <span class="tracking-tight uppercase">Persistiendo Datos en Blockchain Local...</span>
         {:else}
            <svg class="w-7 h-7 group-hover:translate-y-[-2px] transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04M12 21.355r2.263-5.21c.242-.558.118-1.23-.303-1.65l-4.242-4.242a.5.5 0 00-.707 0L4.764 14.494c-.42.42-.544 1.092-.302 1.65l2.263 5.21a.5.5 0 00.915 0L12 16.145l4.36 5.21a.5.5 0 00.915 0z" /></svg>
            <span class="tracking-tight uppercase">Finalizar y Guardar Caracterización</span>
         {/if}
       </button>
       <p class="text-center text-[11px] text-gray-400 font-medium">Al guardar, los datos de escala y la inteligencia técnica del residuo se unificarán en el historial permanente.</p>
    </section>

  </div>
</div>

<Modal isOpen={showModal} title="Cargar para Análisis" onClose={() => showModal = false}>
  <div class="p-8 border-2 border-dashed border-gray-200 rounded-xl text-center hover:border-scientific-400 transition-colors cursor-pointer" on:click={() => document.getElementById('fileIn')?.click()}>
    <input type="file" id="fileIn" class="hidden" accept={uploadOptions.find(o => o.id === currentUploadType)?.accept} on:change={handleFileSelect} />
    <svg class="w-12 h-12 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
    <p class="text-sm font-bold text-gray-700">Selecciona o arrastra el archivo</p>
    <p class="text-xs text-gray-400 mt-1">El análisis se iniciará automáticamente al cargar.</p>
  </div>
</Modal>
