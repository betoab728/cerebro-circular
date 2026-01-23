
<script lang="ts">
  import Navbar from '$lib/components/Navbar.svelte';
  import { API_BASE_URL } from '$lib/config';
  import { fade, slide } from 'svelte/transition';

  let isAnalyzing = $state(false);
  let isSaving = $state(false);
  let records = $state([]);
  let file: File | null = $state(null);
  let successMessage = $state('');
  let errorMessage = $state('');

  async function handleFileUpload(e: Event) {
    const input = e.target as HTMLInputElement;
    if (input.files?.[0]) {
      file = input.files[0];
      await analyzeBatch();
    }
  }

  async function analyzeBatch() {
    if (!file) return;
    isAnalyzing = true;
    records = [];
    errorMessage = '';
    successMessage = '';

    try {
      const data = new FormData();
      data.append('file', file);

      const response = await fetch(`${API_BASE_URL}/analyze-batch`, {
        method: 'POST',
        body: data
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Error en el análisis masivo');
      }

      const result = await response.json();
      records = result.records || [];
    } catch (err) {
      errorMessage = err.message;
    } finally {
      isAnalyzing = false;
    }
  }

  async function saveBatch() {
    if (records.length === 0) return;
    isSaving = true;
    errorMessage = '';
    successMessage = '';

    try {
      const response = await fetch(`${API_BASE_URL}/save-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(records)
      });

      if (!response.ok) throw new Error('Error al guardar los registros');

      const result = await response.json();
      successMessage = `Se han guardado ${result.count} registros exitosamente.`;
      records = [];
      file = null;
    } catch (err) {
      errorMessage = err.message;
    } finally {
      isSaving = false;
    }
  }

  function removeRecord(index: number) {
    records = records.filter((_, i) => i !== index);
  }
</script>

<Navbar title="Carga Masiva de Reportes" />

<div class="p-6 md:p-10 max-w-6xl mx-auto space-y-8 pb-24">
  <header class="text-center space-y-2">
    <h1 class="text-3xl font-extrabold text-gray-900 tracking-tight">Carga Masiva con IA</h1>
    <p class="text-gray-500 max-w-2xl mx-auto text-balance">Carga un informe PDF con tablas de residuos y nuestra IA extraerá automáticamente cada registro para procesarlo en lote.</p>
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

  <!-- UPLOAD SECTION -->
  <section class="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center justify-center space-y-4">
    <div class="w-16 h-16 bg-scientific-50 text-scientific-600 rounded-2xl flex items-center justify-center">
      <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
    </div>
    <div class="text-center">
      <h2 class="text-lg font-bold text-gray-800">Seleccionar Reporte PDF</h2>
      <p class="text-sm text-gray-400">Formatos soportados: .pdf (con tablas de datos)</p>
    </div>
    <label class="cursor-pointer group">
      <input type="file" accept=".pdf" class="hidden" on:change={handleFileUpload} disabled={isAnalyzing} />
      <div class="px-8 py-3 bg-scientific-600 hover:bg-scientific-700 text-white font-bold rounded-xl transition-all active:scale-95 shadow-lg shadow-scientific-100 flex items-center gap-2">
        {isAnalyzing ? 'Procesando...' : 'Elegir Archivo'}
      </div>
    </label>
  </section>

  {#if isAnalyzing}
    <div in:fade class="py-20 flex flex-col items-center justify-center text-center space-y-6">
      <div class="relative w-20 h-20">
        <div class="absolute inset-0 border-4 border-scientific-100 rounded-full"></div>
        <div class="absolute inset-0 border-4 border-scientific-600 rounded-full border-t-transparent animate-spin"></div>
      </div>
      <div class="space-y-1">
        <p class="text-xl font-bold text-gray-800 tracking-tight">Extrayendo Datos con IA</p>
        <p class="text-sm text-gray-400">Analizando tablas y mapeando campos automáticamente...</p>
      </div>
    </div>
  {/if}

  {#if records.length > 0}
    <div in:slide class="space-y-6">
      <div class="flex items-center justify-between">
        <h3 class="text-xl font-bold text-gray-800 flex items-center gap-2">
          <span class="w-6 h-6 bg-scientific-600 text-white rounded-full flex items-center justify-center text-xs">{records.length}</span>
          Registros Detectados
        </h3>
        <button 
          on:click={saveBatch}
          disabled={isSaving}
          class="px-6 py-2.5 bg-black text-white text-sm font-bold rounded-xl hover:bg-gray-800 transition-all flex items-center gap-2 disabled:opacity-50"
        >
          {#if isSaving}
            <svg class="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            Guardando Lote...
          {:else}
            Guardar Todo en Base de Datos
          {/if}
        </button>
      </div>

      <div class="overflow-x-auto bg-white rounded-2xl border border-gray-100 shadow-sm">
        <table class="w-full text-left text-sm min-w-[1200px]">
          <thead>
            <tr class="bg-gray-50/50 text-gray-400 font-bold text-[10px] uppercase tracking-widest border-b border-gray-100">
              <th class="px-6 py-4">Entidad / Planta</th>
              <th class="px-6 py-4">Residuo (Reporte)</th>
              <th class="px-6 py-4 text-scientific-600">Material IA</th>
              <th class="px-6 py-4">Clasificación</th>
              <th class="px-6 py-4 text-right">Cantidad</th>
              <th class="px-6 py-4">Proceso de tratamiento para valorización</th>
              <th class="px-6 py-4">Proceso de tratamiento para reclasificación a no peligroso</th>
              <th class="px-6 py-4 text-center">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            {#each records as rec, i}
              <tr class="group hover:bg-gray-50/50 transition-colors">
                <td class="px-6 py-4">
                  <div class="font-bold text-gray-900 leading-tight">{rec.razon_social ?? 'No especificado'}</div>
                  <div class="text-[10px] text-gray-400 uppercase font-medium">{rec.planta ?? '---'} - {rec.departamento ?? '---'}</div>
                </td>
                <td class="px-6 py-4">
                  <div class="font-medium text-gray-700">{rec.caracteristica ?? 'Sin descripción'}</div>
                  <div class="text-[10px] font-bold text-gray-400 bg-gray-50 inline-block px-1.5 rounded uppercase mt-0.5">{rec.codigo_basilea ?? 'N/A'}</div>
                </td>
                <td class="px-6 py-4">
                  <div class="font-black text-scientific-700 leading-tight uppercase text-xs">{rec.analysis_material_name || 'Pendiente'}</div>
                  <div class="flex gap-1 mt-1">
                    <span class="w-2 h-2 rounded-full bg-scientific-400 animate-pulse"></span>
                    <span class="text-[9px] font-bold text-scientific-500 uppercase tracking-tighter">Caracterizado</span>
                  </div>
                </td>
                <td class="px-6 py-4">
                  <span class="px-2.5 py-1 rounded-full text-[10px] font-black uppercase {rec.tipo_residuo === 'PELIGROSO' ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}">
                    {rec.tipo_residuo}
                  </span>
                </td>
                <td class="px-6 py-4 text-right">
                  <div class="font-black text-gray-900">{rec.cantidad?.toLocaleString() ?? '0'}</div>
                  <div class="text-[10px] text-gray-400 font-bold uppercase">{rec.unidad_medida ?? 'UNID'}</div>
                  <div class="text-[9px] text-scientific-600 font-medium italic">({rec.peso_total ?? 0} kg)</div>
                </td>
                <td class="px-6 py-4 max-w-[300px]">
                  {#if rec.oportunidades_ec && rec.oportunidades_ec !== 'Análisis no disponible'}
                    <div class="bg-scientific-50 border border-scientific-100 p-2.5 rounded-xl">
                      <p class="text-[11px] font-bold text-scientific-700 leading-tight">
                        {rec.oportunidades_ec}
                      </p>
                      <div class="mt-2 text-right border-t border-scientific-100 pt-1">
                        <span class="text-base font-black text-scientific-600">{rec.viabilidad_ec || 0}%</span>
                        <span class="text-[8px] font-bold text-scientific-400 uppercase tracking-tighter italic ml-1">Efectividad</span>
                      </div>
                    </div>
                  {:else}
                    <div class="text-[10px] text-gray-400 italic">Analizando...</div>
                  {/if}
                </td>
                <td class="px-6 py-4 max-w-[300px]">
                  {#if rec.recla_no_peligroso && rec.recla_no_peligroso !== 'No aplica'}
                    <div class="bg-amber-50/50 border border-amber-100 p-2.5 rounded-xl">
                      <p class="text-[11px] font-bold text-amber-700 leading-tight">
                        {rec.recla_no_peligroso}
                      </p>
                    </div>
                  {:else}
                    <span class="text-[10px] font-bold {rec.recla_no_peligroso === 'No aplica' ? 'text-green-500 bg-green-50' : 'text-gray-400 italic'} px-2 py-0.5 rounded">
                      {rec.recla_no_peligroso === 'No aplica' ? 'No requiere' : 'Cargando...'}
                    </span>
                  {/if}
                </td>
                <td class="px-6 py-4 text-center">
                  <button on:click={() => removeRecord(i)} class="p-2 text-gray-300 hover:text-red-500 transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {/if}
</div>
