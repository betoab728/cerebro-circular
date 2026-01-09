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
    responsable: '',
    unidad_generadora: '',
    tipo_residuo: '',
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

      const response = await fetch(`${API_BASE_URL}/analyze`, { method: 'POST', body: data });
      if (!response.ok) throw new Error('Error en el análisis de IA');

      analysisResult = await response.json();
      
      // Auto-fill some form data from AI
      formData.tipo_residuo = analysisResult.category === 'Peligroso' ? 'PELIGROSO' : 'NO PELIGROSO';
      formData.caracteristica = analysisResult.materialName;
      
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
        // Include Analysis Data if available
        analysis_material_name: analysisResult?.materialName,
        analysis_physicochemical: JSON.stringify(analysisResult?.physicochemical),
        analysis_elemental: JSON.stringify(analysisResult?.elemental),
        analysis_engineering: JSON.stringify(analysisResult?.engineeringContext),
        analysis_valorization: JSON.stringify(analysisResult?.valorizationRoutes)
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

<div class="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
  
  {#if successMessage}
    <div transition:fade class="p-4 bg-green-50 text-green-700 rounded-lg border border-green-200 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
        {successMessage}
      </div>
      <a href="/registry" class="text-sm font-bold underline">Ver en Registros Maestros</a>
    </div>
  {/if}

  {#if errorMessage}
    <div transition:fade class="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200 flex items-center gap-2">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
      {errorMessage}
    </div>
  {/if}

  <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
    
    <!-- LEFT: AI Characterization Selection -->
    <div class="space-y-6">
      <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <h2 class="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <svg class="w-6 h-6 text-scientific-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
          1. Análisis de IA del Residuo
        </h2>
        <p class="text-sm text-gray-500 mb-6">Analiza técnicamente el material para obtener sus propiedades antes de registrarlo.</p>

        {#if isAnalyzing}
          <div class="py-12 flex flex-col items-center justify-center text-center space-y-4">
            <svg class="animate-spin h-10 w-10 text-scientific-600" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p class="text-scientific-700 font-medium">Motor de IA procesando material...</p>
          </div>
        {:else if analysisResult}
          <div transition:slide class="space-y-6">
            <!-- HEADER -->
            <div class="bg-scientific-50/30 p-4 rounded-lg border border-scientific-100">
               <div class="flex justify-between items-start">
                 <div>
                   <span class="text-[10px] font-bold uppercase text-scientific-600">Material Detectado</span>
                   <h3 class="text-xl font-bold text-gray-900">{analysisResult.materialName}</h3>
                 </div>
                 <button on:click={() => { analysisResult = null; file = null; }} class="text-xs text-red-500 underline">Cambiar archivo</button>
               </div>
               
               <div class="grid grid-cols-2 gap-4 text-xs mt-3">
                  <div class="bg-white p-2 border border-gray-100 rounded">
                     <span class="text-gray-400 block mb-1">Confianza</span>
                     <span class="font-bold text-green-600">{analysisResult.confidence}%</span>
                  </div>
                  <div class="bg-white p-2 border border-gray-100 rounded">
                     <span class="text-gray-400 block mb-1">Categoría</span>
                     <span class="font-bold">{analysisResult.category}</span>
                  </div>
               </div>
            </div>

            <!-- PHYSICOCHEMICAL -->
            <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Propiedades Físico-Químicas</h4>
              <div class="space-y-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                {#each analysisResult.physicochemical as prop}
                  <div class="flex justify-between text-sm py-2 border-b border-gray-50">
                    <span class="text-gray-500">{prop.name}</span>
                    <span class="font-bold text-gray-900">{prop.value}</span>
                  </div>
                {/each}
              </div>
            </div>

            <!-- ELEMENTAL -->
            <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Composición Elemental</h4>
                <div class="flex flex-wrap gap-2">
                  {#each analysisResult.elemental as el}
                    <div class="bg-gray-50 border border-gray-100 px-3 py-2 rounded text-center min-w-[60px]">
                      <div class="text-[10px] text-gray-400 uppercase">{el.label}</div>
                      <div class="text-sm font-bold text-indigo-600">{el.value}%</div>
                    </div>
                  {/each}
                </div>
                {#if analysisResult.elementalSummary}
                  <p class="text-[11px] text-gray-500 mt-3 italic leading-relaxed">{analysisResult.elementalSummary}</p>
                {/if}
            </div>

            <!-- ENGINEERING -->
            <div class="bg-gradient-to-br from-scientific-50 to-white border border-scientific-100 rounded-xl p-5 shadow-sm">
               <h4 class="text-xs font-bold text-scientific-600 uppercase tracking-wider mb-2">Evaluación de Ingeniería</h4>
               <p class="text-xs text-gray-700 leading-relaxed mb-2">
                 <strong class="font-bold text-gray-900">Estructura:</strong> {analysisResult.engineeringContext.structure}
               </p>
               <p class="text-xs text-gray-700 leading-relaxed">
                 <strong class="font-bold text-gray-900">Procesabilidad:</strong> {analysisResult.engineeringContext.processability}
               </p>
            </div>

            <!-- VALORIZATION -->
            <div class="space-y-3">
              <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider">Rutas de Valorización</h4>
              {#each analysisResult.valorizationRoutes as route}
                <div class="flex items-center gap-3 p-3 rounded-lg border bg-white {route.score >= 90 ? 'border-green-100' : 'border-gray-100'}">
                   <div class="flex-1 min-w-0">
                      <p class="text-[10px] font-bold text-scientific-700 uppercase">{route.method}</p>
                      <p class="text-[9px] text-gray-500 truncate">Output: {route.output}</p>
                   </div>
                   <div class="text-xs font-bold {route.score >= 90 ? 'text-green-600' : 'text-gray-400'}">
                     {route.score}%
                   </div>
                </div>
              {/each}
            </div>
          </div>
        {:else}
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {#each uploadOptions as opt}
              <button on:click={() => openUpload(opt.id)} class="flex flex-col items-center p-4 border rounded-xl hover:border-scientific-400 hover:bg-scientific-50 transition-all group">
                <div class={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${opt.color}`}>
                   <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={opt.icon} /></svg>
                </div>
                <span class="text-xs font-bold text-gray-700">{opt.title}</span>
              </button>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <!-- RIGHT: Waste Generation Form -->
    <div class="bg-white p-6 md:p-8 rounded-xl shadow-lg border-2 border-scientific-100">
       <h2 class="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
         <svg class="w-6 h-6 text-scientific-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
         2. Datos de Registro y Generación
       </h2>

       <form on:submit|preventDefault={handleRegister} class="space-y-5">
         <div>
           <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Responsable</label>
           <input type="text" required bind:value={formData.responsable} class="w-full rounded-lg border-gray-200 focus:border-scientific-500" placeholder="Nombre completo" />
         </div>

         <div class="grid grid-cols-2 gap-4">
           <div>
             <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Unidad Generadora</label>
             <select required bind:value={formData.unidad_generadora} class="w-full rounded-lg border-gray-200">
               <option value="" disabled>Seleccione...</option>
               {#each unidadesGeneradoras as u} <option value={u}>{u}</option> {/each}
             </select>
           </div>
           <div>
             <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Tipo de Residuo</label>
             <select required bind:value={formData.tipo_residuo} class="w-full rounded-lg border-gray-200">
               <option value="" disabled>Seleccione...</option>
               {#each tiposResiduo as t} <option value={t}>{t}</option> {/each}
             </select>
           </div>
         </div>

         <div>
           <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Característica / Descripción</label>
           <textarea required bind:value={formData.caracteristica} rows="2" class="w-full rounded-lg border-gray-200" placeholder="Descripción física del residuo..."></textarea>
         </div>

         <div class="grid grid-cols-3 gap-4">
           <div>
             <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Cantidad</label>
             <input type="number" step="0.01" required bind:value={formData.cantidad} class="w-full rounded-lg border-gray-200" />
           </div>
           <div>
             <label class="block text-xs font-bold text-gray-500 uppercase mb-1">U.M</label>
             <select required bind:value={formData.unidad_medida} class="w-full rounded-lg border-gray-200">
               {#each unidadesMedida as um} <option value={um}>{um}</option> {/each}
             </select>
           </div>
           <div>
             <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Peso (kg)</label>
             <input type="number" step="0.01" required bind:value={formData.peso_total} class="w-full rounded-lg border-gray-200" />
           </div>
         </div>

         <div class="pt-4">
           <button 
             type="submit" 
             disabled={isSaving || isAnalyzing}
             class="w-full bg-scientific-600 hover:bg-scientific-700 text-white font-bold py-4 rounded-xl shadow-lg transition-all flex items-center justify-center gap-3 disabled:opacity-50"
           >
             {#if isSaving}
               <svg class="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
               Procesando Guardado...
             {:else}
               <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" /></svg>
               Guardar y Caracterizar Registro
             {/if}
           </button>
           <p class="text-[10px] text-gray-400 text-center mt-3">Al guardar, la información técnica de la IA se adjuntará permanentemente a este registro de generación.</p>
         </div>
       </form>
    </div>

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
