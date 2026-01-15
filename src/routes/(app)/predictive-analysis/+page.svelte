<script lang="ts">
  import { fade, fly, slide } from 'svelte/transition';
  import { onMount } from 'svelte';
  import { API_BASE_URL } from '$lib/config';

  // --- STORES & STATE ---
  let imageFile: File | null = null;
  let docFile: File | null = null;
  
  let imagePreview: string | null = null;
  let docName: string | null = null;

  let isAnalyzing = false;
  let error: string | null = null;
  let results: any = null;

  // --- HANDLERS ---
  function handleImageSelect(e: Event) {
    const input = e.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      imageFile = input.files[0];
      imagePreview = URL.createObjectURL(imageFile);
    }
  }

  function handleDocSelect(e: Event) {
    const input = e.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      docFile = input.files[0];
      docName = docFile.name; // Basic PDF validation could be here
    }
  }

  async function performAnalysis() {
    if (!imageFile || !docFile) {
        error = "Por favor, sube ambos archivos (Foto y Documento) para iniciar el análisis.";
        return;
    }
    
    isAnalyzing = true;
    error = null;
    results = null;

    try {
        const formData = new FormData();
        formData.append('image', imageFile);
        formData.append('document', docFile);

        const response = await fetch(`${API_BASE_URL}/predictive-analysis`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || "Error en el análisis del servidor");
        }

        results = await response.json();
        console.log("Resultados:", results);

    } catch (err: any) {
        console.error(err);
        error = err.message || "Ocurrió un error inesperado";
    } finally {
        isAnalyzing = false;
    }
  }

  function reset() {
    imageFile = null;
    docFile = null;
    imagePreview = null;
    docName = null;
    results = null;
    error = null;
  }

  async function downloadReport() {
    if (!results) return;
    try {
        const response = await fetch(`${API_BASE_URL}/predictive-report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(results)
        });

        if (!response.ok) throw new Error("Download failed");

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Prediccion_${results.productOverview.productName}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (e) {
        console.error("Report Download Error:", e);
        alert("Error al descargar el reporte.");
    }
  }

  // --- HELPERS FOR UI ---
  // --- REGISTRY FORM ---
  let regDate = new Date().toISOString().split('T')[0];
  let regResponsable = "";
  let regArea = "";
  let regProducto = "";
  let regCantidad = 0;
  let regDescripcion = "";
  let regValorUnit = 0;
  let regValorTotal = 0;
  let regTipoAmbiental = "reciclable"; // reciclable, reutilizable, reaprovechable
  let isSaving = false;
  let saveMessage: { type: 'success' | 'error', text: string } | null = null;
  
  $: if (results) {
      // Pre-fill form when results arrive
      regProducto = results.productOverview.productName || "";
      regDescripcion = results.productOverview.detectedPackaging || "";
      // Try to parse value
      const valStr = results.economicAnalysis.estimatedRecyclingValue || "";
      const match = valStr.match(/[\d\.]+/);
      if (match) {
          regValorUnit = parseFloat(match[0]);
      }
  }

  $: regValorTotal = (regCantidad * regValorUnit) || 0;

  async function saveRegistry() {
      isSaving = true;
      saveMessage = null;
      
      const payload = {
          fecha: new Date(regDate).toISOString(),
          responsable: regResponsable,
          area_solicitante: regArea,
          producto: regProducto,
          cantidad: regCantidad,
          descripcion: regDescripcion,
          valor_economico_unitario: regValorUnit,
          valor_economico_total: regValorTotal,
          tipo_valor_ambiental: regTipoAmbiental,
          analysis_snapshot: JSON.stringify(results)
      };

      try {
          const res = await fetch(`${API_BASE_URL}/predictive-registry`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload)
          });
          
          if (!res.ok) throw new Error("Error al guardar registro");
          
          saveMessage = { type: 'success', text: "Registro guardado exitosamente en base de datos." };
      } catch (e) {
          console.error(e);
          saveMessage = { type: 'error', text: "Fallo al guardar el registro." };
      } finally {
          isSaving = false;
      }
  }

  function getScoreColor(score: number): string {
    if (score >= 80) return 'text-emerald-600 bg-emerald-50 border-emerald-200';
    if (score >= 50) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  }

  function getImpactColor(level: string): string {
    const lower = level.toLowerCase();
    if (lower.includes('low') || lower.includes('bajo')) return 'text-emerald-600 bg-emerald-50';
    if (lower.includes('medium') || lower.includes('medio')) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  }
</script>

<div class="min-h-screen bg-slate-50 p-6 md:p-10 font-sans text-slate-800">

  <!-- HEADER -->
  <header class="mb-10 max-w-5xl mx-auto">
    <div class="flex items-center gap-3 mb-2">
      <span class="text-3xl">🔮</span>
      <h1 class="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
        Análisis Preventivo y Predictivo
      </h1>
    </div>
    <p class="text-slate-500 max-w-xl">
      Sube una fotografía del producto y su hoja de seguridad para predecir su ciclo de vida, impacto ambiental y valor de recuperación antes de la compra.
    </p>
  </header>

  <main class="max-w-5xl mx-auto">
    
    <!-- UPLOAD SECTION -->
    {#if !results && !isAnalyzing}
      <div in:fade={{ duration: 300 }} class="grid md:grid-cols-2 gap-8 mb-8">
        
        <!-- CARD 1: IMAGE -->
        <div class="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow relative group">
           <div class="absolute top-4 right-4 text-slate-200 text-6xl opacity-20 pointer-events-none group-hover:scale-110 transition-transform">📷</div>
           <h3 class="text-lg font-bold mb-4 text-slate-700">1. Fotografía del Producto</h3>
           <p class="text-sm text-slate-400 mb-6">Sube una foto clara del empaque para analizar materiales físicos y diseño.</p>
           
           <input type="file" accept="image/*" on:change={handleImageSelect} class="hidden" id="img-upload"/>
           
           <label for="img-upload" class="flex flex-col items-center justify-center w-full h-48 border-2 border-dashed border-slate-200 rounded-xl cursor-pointer hover:bg-blue-50 hover:border-blue-300 transition-colors bg-slate-50">
              {#if imagePreview}
                <img src={imagePreview} alt="Preview" class="h-full w-full object-contain rounded-lg" />
              {:else}
                <span class="text-3xl mb-2 text-slate-300">+</span>
                <span class="text-sm font-medium text-slate-500">Subir Imagen (JPG/PNG)</span>
              {/if}
           </label>
           {#if imageFile}
             <div class="mt-2 text-xs text-green-600 font-medium flex items-center justify-center">
                ✓ {imageFile.name}
             </div>
           {/if}
        </div>

        <!-- CARD 2: DOCUMENT -->
        <div class="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow relative group">
           <div class="absolute top-4 right-4 text-slate-200 text-6xl opacity-20 pointer-events-none group-hover:scale-110 transition-transform">📄</div>
           <h3 class="text-lg font-bold mb-4 text-slate-700">2. Ficha Técnica / MSDS</h3>
           <p class="text-sm text-slate-400 mb-6">Sube el PDF con la composición química y datos de seguridad.</p>
           
           <input type="file" accept=".pdf" on:change={handleDocSelect} class="hidden" id="doc-upload"/>
           
           <label for="doc-upload" class="flex flex-col items-center justify-center w-full h-48 border-2 border-dashed border-slate-200 rounded-xl cursor-pointer hover:bg-purple-50 hover:border-purple-300 transition-colors bg-slate-50">
              {#if docName}
                <div class="text-center">
                    <span class="text-4xl block mb-2">📄</span>
                    <span class="text-sm font-medium text-slate-700">{docName}</span>
                </div>
              {:else}
                <span class="text-3xl mb-2 text-slate-300">+</span>
                <span class="text-sm font-medium text-slate-500">Subir PDF</span>
              {/if}
           </label>
           {#if docFile}
             <div class="mt-2 text-xs text-green-600 font-medium flex items-center justify-center">
                ✓ Archivo seleccionado
             </div>
           {/if}
        </div>

      </div>

      <!-- ACTION BUTTON -->
      <div class="flex flex-col items-center justify-center">
        {#if error}
            <div class="mb-4 text-red-500 bg-red-50 px-4 py-2 rounded-lg text-sm">{error}</div>
        {/if}
        <button 
            on:click={performAnalysis}
            disabled={!imageFile || !docFile}
            class="group relative px-8 py-4 bg-slate-900 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95 transition-all overflow-hidden"
        >
            <div class="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <span class="relative flex items-center gap-2">
                Generar Predicción Inteligente
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            </span>
        </button>
      </div>

    {/if}

    <!-- LOADING STATE -->
    {#if isAnalyzing}
      <div in:fade class="flex flex-col items-center justify-center min-h-[400px]">
        <div class="w-20 h-20 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin mb-8"></div>
        <h2 class="text-2xl font-bold text-slate-700 mb-2">Analizando Ciclo de Vida...</h2>
        <p class="text-slate-500">Nuestros modelos están cruzando datos visuales y químicos.</p>
        <div class="flex gap-4 mt-8 opacity-50">
            <span class="animate-pulse">🧪 Química</span>
            <span class="animate-pulse delay-75">📦 Materiales</span>
            <span class="animate-pulse delay-150">💰 Economía</span>
        </div>
      </div>
    {/if}

    <!-- RESULTS DASHBOARD -->
    {#if results}
      <div in:slide={{ duration: 600, axis: 'y' }} class="space-y-8 pb-20">
        
        <!-- TOP BAR: PRODUCT IDENTITY -->
        <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
                <div class="text-xs font-bold text-blue-600 uppercase tracking-widest mb-1">Análisis Completado</div>
                <h2 class="text-2xl font-bold text-slate-800">{results.productOverview.productName}</h2>
            </div>
            <div class="flex gap-3 text-sm">
                <div class="px-3 py-1 bg-slate-100 rounded-full text-slate-600 border border-slate-200">
                    📦 {results.productOverview.detectedPackaging}
                </div>
                <div class="px-3 py-1 bg-slate-100 rounded-full text-slate-600 border border-slate-200">
                    🧪 {results.productOverview.detectedContent}
                </div>
            </div>
            <div class="flex gap-4">
                <button on:click={downloadReport} class="text-sm font-medium text-blue-600 hover:text-blue-800 flex items-center gap-1">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                    Descargar Informe
                </button>
                <button on:click={reset} class="text-sm text-slate-400 hover:text-slate-600 underline">Nuevo Análisis</button>
            </div>
        </div>

        <!-- 3 PILLARS GRID -->
        <div class="grid md:grid-cols-3 gap-6">
            
            <!-- 1. TECHNICAL LIFE -->
            <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 relative overflow-hidden">
                <div class="absolute top-0 right-0 w-24 h-24 bg-blue-50 rounded-bl-full -mr-4 -mt-4 z-0"></div>
                <div class="relative z-10">
                    <div class="flex items-center gap-2 mb-6">
                        <span class="p-2 bg-blue-100 text-blue-600 rounded-lg">⚙️</span>
                        <h3 class="font-bold text-slate-700">Vida Útil Técnica</h3>
                    </div>
                    
                    <div class="mb-4">
                        <div class="text-xs text-slate-400 uppercase mb-1">Durabilidad Estimada</div>
                        <div class="text-2xl font-bold text-slate-800">{results.lifecycleMetrics.estimatedLifespan}</div>
                    </div>

                    <div class="mb-4">
                        <div class="flex justify-between text-xs mb-1">
                            <span class="text-slate-500">Score de Durabilidad</span>
                            <span class="font-bold">{results.lifecycleMetrics.durabilityScore}/100</span>
                        </div>
                        <div class="w-full bg-slate-100 rounded-full h-2">
                            <div class="bg-blue-500 h-2 rounded-full" style="width: {results.lifecycleMetrics.durabilityScore}%"></div>
                        </div>
                        <p class="text-[10px] text-slate-400 mt-2 text-justify leading-tight">
                            * El score (0-100) indica la <b>integridad estructural</b> y <b>potencial de reutilización</b>.
                            <br>
                            <span class="opacity-75">100 = Altamente reutilizable. 0 = Un solo uso.</span>
                        </p>
                    </div>
                    
                    <div class="p-3 bg-slate-50 rounded-lg text-xs text-slate-600 leading-relaxed border border-slate-100">
                        {results.lifecycleMetrics.disposalStage}
                    </div>
                </div>
            </div>

            <!-- 2. ENVIRONMENTAL IMPACT -->
            <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 relative overflow-hidden">
                <div class="absolute top-0 right-0 w-24 h-24 bg-green-50 rounded-bl-full -mr-4 -mt-4 z-0"></div>
                <div class="relative z-10">
                    <div class="flex items-center gap-2 mb-6">
                        <span class="p-2 bg-emerald-100 text-emerald-600 rounded-lg">🌱</span>
                        <h3 class="font-bold text-slate-700">Impacto Ambiental</h3>
                    </div>

                    <div class="mb-4">
                        <div class="text-xs text-slate-400 uppercase mb-1">Huella de Carbono</div>
                        <div class={`inline-block px-3 py-1 rounded-full text-sm font-bold ${getImpactColor(results.environmentalImpact.carbonFootprintLevel)}`}>
                            {results.environmentalImpact.carbonFootprintLevel}
                        </div>
                    </div>
                    
                    <div class="space-y-3">
                         <div class="flex justify-between items-center text-sm border-b border-slate-50 pb-2">
                            <span class="text-slate-500">Peligrosidad</span>
                            <span class="font-medium text-slate-700">{results.environmentalImpact.hazardLevel}</span>
                         </div>
                         <div class="text-sm">
                            <span class="text-slate-500 block mb-1">Potencial de Reciclado:</span>
                            <p class="text-slate-700 text-xs leading-relaxed">{results.environmentalImpact.recycledContentPotential}</p>
                         </div>
                    </div>
                </div>
            </div>

            <!-- 3. ECONOMIC VALUE -->
            <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 relative overflow-hidden">
                <div class="absolute top-0 right-0 w-24 h-24 bg-amber-50 rounded-bl-full -mr-4 -mt-4 z-0"></div>
                <div class="relative z-10">
                    <div class="flex items-center gap-2 mb-6">
                        <span class="p-2 bg-amber-100 text-amber-600 rounded-lg">💰</span>
                        <h3 class="font-bold text-slate-700">Valor Económico</h3>
                    </div>

                    <div class="mb-4">
                         <div class="text-xs text-slate-400 uppercase mb-1">Valor Recuperable Est.</div>
                         <div class="text-2xl font-bold text-slate-800">{results.economicAnalysis.estimatedRecyclingValue}</div>
                    </div>

                    <div class="p-4 bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl border border-amber-100 mb-2">
                        <div class="text-xs font-bold text-amber-800 uppercase mb-1">Recomendación</div>
                        <p class="text-sm text-amber-900 font-medium">{results.economicAnalysis.costBenefitAction}</p>
                    </div>
                     <span class="text-xs text-slate-400">Basado en demanda actual de mercado</span>
                </div>
            </div>

        </div>

        <!-- STRATEGY CONCLUSION -->
        <div class="bg-slate-900 text-white p-8 rounded-3xl shadow-xl relative overflow-hidden">
             <div class="absolute top-0 right-0 w-64 h-64 bg-blue-600 rounded-full blur-[100px] opacity-20 pointer-events-none"></div>
             <div class="relative z-10 flex flex-col md:flex-row gap-8 items-start">
                 <div class="flex-1">
                     <h3 class="text-blue-300 font-bold uppercase tracking-wider text-sm mb-2">Estrategia Circular Recomendada</h3>
                     <div class="text-3xl font-bold mb-4">{results.circularStrategy.recommendedRoute}</div>
                     <p class="text-slate-300 leading-relaxed max-w-2xl">
                         {results.circularStrategy.justification}
                     </p>
                 </div>
                 <div class="min-w-[150px]">
                     <div class="w-full aspect-square rounded-2xl bg-white/10 border border-white/20 flex flex-col items-center justify-center p-4 text-center">
                        <span class="text-4xl mb-2">🔄</span>
                        <span class="text-xs font-medium text-blue-200">Cierre de Ciclo</span>
                     </div>
                 </div>
             </div>
        </div>

        <!-- REGISTRATION FORM -->
        <div class="bg-white p-8 rounded-3xl shadow-sm border border-slate-200 mt-8">
            <h3 class="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
                📂 Registro de Gestión de Residuos
            </h3>
            
            <div class="grid md:grid-cols-2 gap-6">
                <!-- Fecha -->
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Fecha</label>
                    <input type="date" bind:value={regDate} class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>
                
                <!-- Responsable -->
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Responsable</label>
                    <input type="text" bind:value={regResponsable} placeholder="Nombre del responsable" class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>

                <!-- Area Solicitante -->
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Área Solicitante</label>
                    <input type="text" bind:value={regArea} placeholder="Ej: Logística" class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>

                <!-- Producto -->
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Producto</label>
                    <input type="text" bind:value={regProducto} class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>

                <!-- Cantidad -->
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Cantidad</label>
                    <input type="number" bind:value={regCantidad} min="0" step="0.1" class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>

                <!-- Descripcion -->
                <div class="md:col-span-2">
                    <label class="block text-sm font-medium text-slate-700 mb-1">Descripción</label>
                    <input type="text" bind:value={regDescripcion} class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>

                <!-- Valor Unitario -->
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Valor Unitario (S/.)</label>
                    <input type="number" bind:value={regValorUnit} min="0" step="0.01" class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>

                <!-- Valor Total (Readonly) -->
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Valor Total (S/.)</label>
                    <input type="text" value={regValorTotal.toFixed(2)} readonly class="w-full px-4 py-2 bg-slate-100 border border-slate-300 rounded-lg text-slate-600 cursor-not-allowed" />
                </div>

                <!-- Tipo Valor Ambiental -->
                <div class="md:col-span-2">
                    <label class="block text-sm font-medium text-slate-700 mb-1">Tipo Valor Ambiental</label>
                    <select bind:value={regTipoAmbiental} class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white">
                        <option value="reciclable">Reciclable</option>
                        <option value="reutilizable">Reutilizable</option>
                        <option value="reaprovechable">Reaprovechable</option>
                    </select>
                </div>
            </div>

            <!-- Boton Guardar -->
            <div class="mt-8 flex flex-col items-center">
                {#if saveMessage}
                    <div class={`mb-4 px-4 py-2 rounded-lg text-sm ${saveMessage.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {saveMessage.text}
                    </div>
                {/if}
                
                <button 
                    on:click={saveRegistry}
                    disabled={isSaving}
                    class="px-8 py-3 bg-blue-600 text-white font-bold rounded-xl shadow-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isSaving ? 'Guardando...' : '💾 Guardar Registro en Base de Datos'}
                </button>
            </div>
        </div>

      </div>
    {/if}

  </main>
</div>
