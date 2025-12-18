<script lang="ts">
  import Navbar from '$lib/components/Navbar.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import { PUBLIC_API_URL } from '$env/static/public';

  // Analysis State
  let isAnalyzing = false;
  let analysisResult: any = null;

  // Upload/Modal State
  let showModal = false;
  let currentUploadType = ''; // 'technical', 'security', 'photo'
  let dragging = false;
  let file: File | null = null;

  const uploadOptions = [
    { 
      id: 'technical', 
      title: 'Ficha Técnica', 
      desc: 'PDF con especificaciones del fabricante', 
      icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      color: 'bg-blue-50 text-blue-600',
      accept: '.pdf,.doc,.docx'
    },
    { 
      id: 'security', 
      title: 'Hoja de Seguridad', 
      desc: 'MSDS / HDS con datos de peligrosidad', 
      icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
      color: 'bg-amber-50 text-amber-600',
      accept: '.pdf'
    },
    { 
      id: 'photo', 
      title: 'Fotografía del Residuo', 
      desc: 'Análisis visual por IA (Visión Computacional)', 
      icon: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z',
      color: 'bg-purple-50 text-purple-600',
      accept: 'image/*'
    }
  ];

  function openUpload(typeId: string) {
    currentUploadType = typeId;
    file = null;
    showModal = true;
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    dragging = false;
    if (e.dataTransfer?.files && e.dataTransfer.files[0]) {
      file = e.dataTransfer.files[0];
      setTimeout(() => { showModal = false; startAnalysis(); }, 800);
    }
  }

  function handleFileSelect(e: Event) {
    const input = e.target as HTMLInputElement;
    if (input.files && input.files[0]) {
       file = input.files[0];
       setTimeout(() => { showModal = false; startAnalysis(); }, 800);
    }
  }

  async function startAnalysis() {
    if (!file) {
      console.warn("No file selected");
      return;
    }

    isAnalyzing = true;
    analysisResult = null;
    
    console.log(`[Frontend] Starting Analysis. Type: ${currentUploadType}, File: ${file.name}`);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('type', currentUploadType);

      console.log("[Frontend] Sending request to Backend...");
      const response = await fetch(`${PUBLIC_API_URL}/analyze`, {
        method: 'POST',
        body: formData
      }); 

      console.log(`[Frontend] Response Status: ${response.status}`);
      
      if (!response.ok) {
        const errText = await response.text();
        console.error(`[Frontend] Error Body: ${errText}`);
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      console.log("[Frontend] parsing JSON...");
      analysisResult = await response.json();
      console.log("[Frontend] Analysis Result:", analysisResult);
      
    } catch (err) {
      console.error("[Frontend] Analysis Failed:", err);
      alert(`Error: ${err.message}`);
    } finally {
      console.log("[Frontend] Finished. Setting isAnalyzing = false");
      isAnalyzing = false;
    }
  }

  async function downloadReport() {
    if (!analysisResult) return;
    try {
        const response = await fetch(`${PUBLIC_API_URL}/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(analysisResult)
        });

        if (!response.ok) throw new Error("Download failed");

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Informe_Tecnico_${analysisResult.materialName}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (e) {
        console.error("Report Download Error:", e);
        alert("Error al descargar el reporte.");
    }
  }
</script>

<Navbar title="Selección Inteligente & Caracterización" />

<div class="p-6 md:p-8 grid grid-cols-1 lg:grid-cols-3 gap-8 pb-12">
  
  <!-- Left Panel: Input / Upload Selection -->
  <div class="lg:col-span-1 flex flex-col gap-6">
    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
      <h3 class="text-lg font-semibold text-gray-800 mb-4">Fuente de Información</h3>
      <p class="text-sm text-gray-500 mb-6">Selecciona el tipo de documento o archivo para iniciar la caracterización del residuo.</p>
      
      <div class="space-y-4">
        {#each uploadOptions as option}
          <button 
            class="w-full flex items-center p-4 rounded-xl border border-gray-200/60 hover:border-scientific-300 hover:bg-scientific-50/50 transition-all group text-left shadow-sm hover:shadow-md"
            on:click={() => openUpload(option.id)}
          >
            <div class={`w-12 h-12 rounded-lg flex items-center justify-center shrink-0 ${option.color} mr-4 transition-transform group-hover:scale-110`}>
               <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={option.icon} /></svg>
            </div>
            <div>
              <h4 class="font-semibold text-gray-800 group-hover:text-scientific-700 transition-colors">{option.title}</h4>
              <p class="text-xs text-gray-500 mt-0.5">{option.desc}</p>
            </div>
            <div class="ml-auto opacity-0 group-hover:opacity-100 transition-opacity text-scientific-500">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
            </div>
          </button>
        {/each}
      </div>
    </div>

    <!-- Manual Input Option (Collapsed/Secondary) -->
    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex-1 opacity-80 hover:opacity-100 transition-opacity">
      <h3 class="text-lg font-semibold text-gray-800 mb-2">Ingreso Manual</h3>
      <p class="text-xs text-gray-400 mb-4">Si no dispones de archivos, ingresa los datos básicos.</p>
      <button class="w-full bg-gray-50 hover:bg-gray-100 text-gray-600 font-medium py-2 rounded-lg border border-gray-200 transition-colors text-sm">
         Abrir Formulario Manual
      </button>
    </div>
  </div>

  <!-- Right Panel: Results -->
  <div class="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 p-8 flex flex-col relative overflow-hidden min-h-[600px]">
    {#if isAnalyzing}
      <div class="absolute inset-0 bg-white/95 z-20 flex flex-col items-center justify-center text-center px-4">
         <div class="relative w-24 h-24 mb-6">
           <div class="absolute inset-0 border-4 border-gray-100 rounded-full"></div>
           <div class="absolute inset-0 border-4 border-scientific-500 rounded-full border-t-transparent animate-spin"></div>
           <svg class="absolute inset-0 m-auto w-10 h-10 text-scientific-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
         </div>
         <h3 class="text-lg font-semibold text-gray-900 mb-2">Procesando {currentUploadType === 'photo' ? 'Imagen Espectral' : 'Documento Técnico'}...</h3>
         <div class="space-y-1 text-sm text-gray-500">
           <p class="animate-pulse delay-75">Extrayendo estructura molecular...</p>
           <p class="animate-pulse delay-150">Calculando cristalinidad y densidad...</p>
           <p class="animate-pulse delay-300">Cruzando con base de datos de Ciencia de Materiales...</p>
         </div>
      </div>
    {/if}

    {#if analysisResult}
      <div class="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        
        <!-- Result Header -->
        <div class="border-b border-gray-100 pb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div class="flex items-center gap-3 mb-2">
              <span class="bg-scientific-100 text-scientific-800 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide">{analysisResult.category}</span>
              <span class="flex items-center gap-1 text-green-600 text-xs font-medium bg-green-50 px-2 py-0.5 rounded border border-green-100">
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4" /></svg>
                Confianza IA: {analysisResult.confidence}%
              </span>
            </div>
            <h2 class="text-3xl font-bold text-gray-900">{analysisResult.materialName}</h2>
          </div>
          <div class="text-right">
             <button on:click={downloadReport} class="text-sm text-scientific-600 hover:text-scientific-800 font-medium underline">Descargar Informe Téc.</button>
          </div>
        </div>

        <!-- Material Science Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          
          <!-- Column 1: Physicochemical Properties -->
          <div class="space-y-6">
            <h3 class="text-lg font-semibold text-gray-800 flex items-center gap-2">
              <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
              Propiedades Físico-Químicas
            </h3>
            <div class="bg-gray-50 rounded-xl overflow-hidden border border-gray-200">
              <table class="w-full text-sm text-left">
                <thead class="bg-gray-100 text-gray-500 font-medium text-xs uppercase">
                  <tr>
                    <th class="px-4 py-3">Propiedad</th>
                    <th class="px-4 py-3">Valor Detectado</th>
                    <th class="px-4 py-3 text-right">Método Est.</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                  {#each analysisResult.physicochemical as prop}
                    <tr class="hover:bg-white transition-colors">
                      <td class="px-4 py-3 font-medium text-gray-700">{prop.name}</td>
                      <td class="px-4 py-3 text-gray-900 font-bold">{prop.value}</td>
                      <td class="px-4 py-3 text-right text-gray-400 text-xs">{prop.method}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>

            <!-- Elemental Composition -->
            <div>
              <h4 class="text-sm font-semibold text-gray-500 mb-3 uppercase tracking-wider">Composición Elemental</h4>
              <div class="flex gap-2">
                {#each analysisResult.elemental as el}
                  <div class="flex-1 bg-white border border-gray-200 rounded-lg p-3 text-center shadow-sm">
                    <div class="text-xs text-gray-400 mb-1">{el.label}</div>
                    <div class="text-xl font-bold {el.value > 0 ? 'text-gray-800' : 'text-gray-300'}">
                      {el.value}%
                    </div>
                  </div>
                {/each}
              </div>
            </div>
          </div>

          <!-- Column 2: Engineering & Valorization -->
          <div class="space-y-6">
            <div class="bg-gradient-to-br from-scientific-50 to-white border border-scientific-100 rounded-xl p-6 shadow-sm">
               <h3 class="text-lg font-semibold text-scientific-800 mb-3">Evaluación de Ingeniería</h3>
               <p class="text-sm text-gray-700 leading-relaxed mb-4">
                 <strong class="font-medium text-gray-900">Estructura:</strong> {analysisResult.engineeringContext.structure}
               </p>
               <p class="text-sm text-gray-700 leading-relaxed">
                 <strong class="font-medium text-gray-900">Procesabilidad:</strong> {analysisResult.engineeringContext.processability}
               </p>
            </div>

            <h3 class="text-lg font-semibold text-gray-800 flex items-center gap-2">
              <svg class="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              Rutas de Valorización (Economía Circular)
            </h3>
            
            <div class="space-y-3">
              {#each analysisResult.valorizationRoutes as route}
                <div class="flex items-start gap-4 p-4 rounded-xl border transition-all
                  {route.score >= 90 ? 'bg-green-50 border-green-200' : 
                   route.score >= 60 ? 'bg-white border-gray-200' : 'bg-red-50 border-red-100 opacity-60'}">
                   
                   <div class="flex-1">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="text-xs font-bold uppercase tracking-wider 
                          {route.score >= 90 ? 'text-green-700' : 
                          route.score >= 60 ? 'text-scientific-700' : 'text-red-700'}">{route.role}</span>
                      </div>
                      <h4 class="font-bold text-gray-900">{route.method}</h4>
                      <p class="text-sm text-gray-600 mt-1">Output: {route.output}</p>
                   </div>
                   <div class="text-center">
                     <div class="radial-progress text-xs font-bold 
                        {route.score >= 90 ? 'text-green-600' : 'text-gray-400'}" 
                        style="--value:{route.score}; --size:2.5rem;">
                       {route.score}%
                     </div>
                   </div>
                </div>
              {/each}
            </div>
          </div>

        </div>

      </div>
    {:else if !isAnalyzing}
      <div class="flex-1 flex flex-col items-center justify-center text-center opacity-40">
        <div class="bg-gray-50 p-6 rounded-full mb-4">
           <svg class="w-16 h-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
        </div>
        <p class="text-xl font-medium text-gray-500">Esperando datos para caracterización</p>
        <p class="text-sm text-gray-400 mt-2 max-w-sm">
          Sube una Ficha Técnica, Hoja de Seguridad o Foto para que el motor de IA analice las propiedades materiales.
        </p>
      </div>
    {/if}
  </div>
</div>

<!-- Upload Modal -->
<Modal isOpen={showModal} title={uploadOptions.find(o => o.id === currentUploadType)?.title || 'Cargar Archivo'} onClose={() => showModal = false}>
  <div 
    class="border-2 border-dashed rounded-xl h-48 flex flex-col items-center justify-center transition-all duration-200 cursor-pointer
    {dragging ? 'border-scientific-500 bg-scientific-50' : 'border-gray-300 hover:border-scientific-400 hover:bg-gray-50'}"
    role="button"
    tabindex="0"
    on:drop={handleDrop}
    on:dragover={(e) => { e.preventDefault(); dragging = true; }}
    on:dragleave={() => dragging = false}
    on:click={() => document.getElementById('fileInput')?.click()}
  >
    <input 
      type="file" 
      id="fileInput" 
      class="hidden" 
      accept={uploadOptions.find(o => o.id === currentUploadType)?.accept}
      on:change={handleFileSelect}
    />
    
    {#if file}
      <div class="text-center p-4">
        <div class="w-10 h-10 rounded-full bg-green-100 text-green-600 flex items-center justify-center mx-auto mb-2">
           <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
        </div>
        <p class="text-sm font-medium text-gray-900">¡Archivo listo!</p>
        <p class="text-xs text-gray-500">Iniciando análisis...</p>
      </div>
    {:else}
      <div class="text-center p-4">
        <svg class="w-10 h-10 text-gray-300 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
        <p class="text-sm font-medium text-gray-600">Arrastra tu archivo aquí</p>
        <p class="text-xs text-gray-400 mt-1">o haz clic para explorar</p>
        <p class="text-xs text-scientific-500 mt-2 font-medium">Compatible: {uploadOptions.find(o => o.id === currentUploadType)?.accept}</p>
      </div>
    {/if}
  </div>
</Modal>

