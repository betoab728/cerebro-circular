
<script lang="ts">
  import Navbar from '$lib/components/Navbar.svelte';
  import { API_BASE_URL } from '$lib/config';
  import { fade, slide } from 'svelte/transition';
  import { browser } from '$app/environment';

  // --- EXPORT LIBS (Lazy Load) ---
  let xlsxLoaded = $state(false);
  let pdfLoaded = $state(false);

  let isAnalyzing = $state(false);
  let isSaving = $state(false);
  let records = $state([]);
  let file: File | null = $state(null);
  let successMessage = $state('');
  let errorMessage = $state('');
  let unidadMinera = $state('');
  let globalResponsable = $state('');

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
      // PHASE 1: Rapid Skeleton Extraction
      const data = new FormData();
      data.append('file', file);

      const extractResponse = await fetch(`${API_BASE_URL}/extract-rows`, {
        method: 'POST',
        body: data
      });

      if (!extractResponse.ok) {
        const err = await extractResponse.json();
        throw new Error(err.detail || 'Error en la extracción de filas');
      }

      const extractResult = await extractResponse.json();
      unidadMinera = extractResult.unidad_minera || 'UNIDAD MINERA NO DETECTADA';
      records = (extractResult.records || []).map(r => ({
        ...r,
        responsable: globalResponsable || 'Sistema IA',
        unidad_generadora: unidadMinera,
        cantidad: r.cantidad || 0,
        unidad_medida: r.unidad_medida || 'OTRO',
        _isCharacterizing: true, 
        oportunidades_ec: 'Analizando...',
        recla_no_peligroso: 'Analizando...'
      }));
      
      isAnalyzing = false; // Hide global spinner, show table

      // PHASE 2: Iterative Deep Characterization
      const chunkSize = 5;
      for (let i = 0; i < records.length; i += chunkSize) {
        const chunk = records.slice(i, i + chunkSize);
        
        try {
          const charResponse = await fetch(`${API_BASE_URL}/characterize-rows`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(chunk)
          });

          if (charResponse.ok) {
            const charResult = await charResponse.json();
            const enriched = charResult.records || [];
            
            // Update the records reactively (MERGE logic to prevent data loss)
            records = records.map(r => {
              const matched = enriched.find(e => e.item_num === r.item_num);
              if (matched) {
                return { ...r, ...matched, _isCharacterizing: false };
              }
              return r;
            });
          }
        } catch (charErr) {
          console.error(`Error characterizing chunk ${i}:`, charErr);
          // We don't stop the whole process if one chunk fails
          records = records.map((r, idx) => {
             if (idx >= i && idx < i + chunkSize) {
               return { ...r, _isCharacterizing: false, oportunidades_ec: 'Error', recla_no_peligroso: 'Error' };
             }
             return r;
          });
        }
      }
    } catch (err) {
      errorMessage = err.message;
      isAnalyzing = false;
    }
  }

  async function saveBatch() {
    if (records.length === 0) return;
    isSaving = true;
    errorMessage = '';
    successMessage = '';

    try {
      // Clean records before sending (optimize payload)
      const payload = records.map(r => {
        const { _isCharacterizing, ...clean } = r;
        return {
          ...clean,
          responsable: globalResponsable || clean.responsable || 'Sistema IA',
          unidad_generadora: unidadMinera || clean.unidad_generadora || 'NO ESPECIFICADO'
        };
      });

      const response = await fetch(`${API_BASE_URL}/save-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Error al guardar los registros');
      }

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

  function exportToExcel() {
    if (!browser || !window.XLSX) return;
    if (records.length === 0) {
      errorMessage = "No hay registros cargados para exportar.";
      return;
    }
    const data = records.map((r, i) => ({
      'N': i + 1,
      'Clasificación': r.tipo_residuo || '-',
      'Código de Basilea': r.codigo_basilea || 'N/A',
      'Descripción': r.caracteristica || 'Sin descripción',
      'Material IA': r.analysis_material_name || 'Pendiente',
      'Total en Toneladas': (Number(r.peso_total || 0) / 1000).toFixed(3),
      'Proceso de Valorización': r.oportunidades_ec && r.oportunidades_ec !== 'Análisis no disponible' 
        ? `${r.oportunidades_ec} (Efectividad: ${r.viabilidad_ec || 0}%)` 
        : 'Analizando...',
      'Proceso de Reclasificación': r.recla_no_peligroso && r.recla_no_peligroso !== 'No aplica'
        ? `${r.recla_no_peligroso} (Probabilidad: ${r.viabilidad_reclasificacion || 0}%)`
        : (r.recla_no_peligroso === 'No aplica' ? 'No requiere' : 'Analizando...'),
      'Unidad Minera': unidadMinera
    }));

    const ws = window.XLSX.utils.json_to_sheet(data);
    const wb = window.XLSX.utils.book_new();
    window.XLSX.utils.book_append_sheet(wb, ws, "Resultados IA");
    
    // Auto-size columns (basic attempt)
    const wscols = [
      {wch: 5}, {wch: 15}, {wch: 15}, {wch: 40}, {wch: 25}, {wch: 15}, {wch: 50}, {wch: 50}, {wch: 20}
    ];
    ws['!cols'] = wscols;

    const date = new Date().toISOString().split('T')[0];
    window.XLSX.writeFile(wb, `Analisis_IA_${unidadMinera}_${date}.xlsx`);
  }

  function exportToPDF() {
    if (!browser || !window.jspdf) {
      errorMessage = "La librería de PDF aún no ha cargado. Reintente en unos segundos.";
      return;
    }
    if (records.length === 0) {
      errorMessage = "No hay registros cargados para exportar.";
      return;
    }
    
    const doc = new window.jspdf.jsPDF('l', 'mm', 'a4');
    
    // Header
    doc.setFontSize(18);
    doc.setTextColor(48, 102, 190);
    doc.text("Reporte de Análisis IA - Cargas Masivas", 14, 22);
    
    doc.setFontSize(11);
    doc.setTextColor(100);
    doc.text(`Unidad Minera: ${unidadMinera}`, 14, 30);
    doc.text(`Responsable del Lote: ${globalResponsable || 'Sistema IA'}`, 14, 35);
    doc.text(`Fecha de Generación: ${new Date().toLocaleString()}`, 14, 40);

    const tableData = records.map((r, i) => [
      i + 1,
      r.tipo_residuo || '-',
      r.caracteristica || '-',
      r.analysis_material_name || 'Pendiente',
      (Number(r.peso_total || 0) / 1000).toFixed(3),
      r.oportunidades_ec && r.oportunidades_ec !== 'Análisis no disponible' 
        ? `${r.oportunidades_ec}\n(${r.viabilidad_ec}% viab.)` 
        : 'Analizando...',
      r.recla_no_peligroso === 'No aplica' ? 'No requiere' : (r.recla_no_peligroso || 'Analizando...')
    ]);

    window.jspdf.autoTable(doc, {
      startY: 45,
      head: [['N', 'Clasif.', 'Descripción de Origen', 'Material IA', 'Ton', 'Oportunidades EC', 'Reclasificación']],
      body: tableData,
      theme: 'grid',
      headStyles: { fillColor: [48, 102, 190], fontSize: 9, halign: 'center' },
      bodyStyles: { fontSize: 7, valign: 'middle' },
      columnStyles: {
        2: { cellWidth: 40 },
        5: { cellWidth: 50 },
        6: { cellWidth: 40 }
      }
    });

    const date = new Date().toISOString().split('T')[0];
    doc.save(`Analisis_IA_${unidadMinera}_${date}.pdf`);
  }

  function removeRecord(index: number) {
    records = records.filter((_, i) => i !== index);
  }
</script>

<svelte:head>
  <script src="https://cdn.sheetjs.com/xlsx-latest/package/dist/xlsx.full.min.js" onload={() => xlsxLoaded = true}></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js" onload={() => pdfLoaded = true}></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js"></script>
</svelte:head>

<Navbar title="Carga Masiva de Reportes" />

<div class="p-6 md:p-10 max-w-6xl mx-auto space-y-8 pb-24">
  <header class="flex flex-col md:flex-row items-center justify-between gap-6 bg-white p-8 rounded-3xl border border-gray-100 shadow-sm">
    <div class="space-y-1 text-center md:text-left">
      <h1 class="text-3xl font-extrabold text-gray-900 tracking-tight text-balance">Carga Masiva con IA</h1>
      <p class="text-gray-500 text-sm">Procesamiento por lote de informes técnicos PDF.</p>
    </div>
    
    <div class="hidden md:block">
      <span class="text-xs font-bold text-gray-400 uppercase tracking-widest bg-gray-50 px-3 py-1 rounded-lg border border-gray-100 italic">Pre-procesamiento con Gemini 2.0</span>
    </div>
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

  <!-- GLOBAL CONFIG -->
  <section class="bg-scientific-50/30 p-6 rounded-2xl border border-scientific-100 flex flex-col md:flex-row items-center gap-6">
    <div class="flex-1 space-y-1">
      <label class="block text-[10px] font-black uppercase tracking-widest text-scientific-600">Responsable del Lote</label>
      <input 
        type="text" 
        bind:value={globalResponsable} 
        placeholder="Ingrese el nombre del responsable..." 
        class="w-full h-12 rounded-xl border-gray-200 focus:ring-4 focus:ring-scientific-50/50 focus:border-scientific-400 transition-all px-4 font-bold text-gray-700"
      />
    </div>
    <div class="flex-1 space-y-1">
      <label class="block text-[10px] font-black uppercase tracking-widest text-scientific-600">Unidad Generadora (Detectada)</label>
      <div class="h-12 flex items-center px-4 bg-white border border-gray-200 rounded-xl font-black text-xs text-scientific-800 uppercase italic">
        {unidadMinera || 'Esperando carga...'}
      </div>
    </div>
  </section>

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
      <input type="file" accept=".pdf" class="hidden" onchange={handleFileUpload} disabled={isAnalyzing} />
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
        <div class="flex flex-wrap items-center gap-3">
          <button 
            onclick={exportToExcel}
            class="px-5 py-2.5 bg-green-600 text-white text-sm font-bold rounded-xl hover:bg-green-700 transition-all flex items-center gap-2 shadow-lg shadow-green-100"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            EXCEL
          </button>
          <button 
            onclick={exportToPDF}
            class="px-5 py-2.5 bg-red-600 text-white text-sm font-bold rounded-xl hover:bg-red-700 transition-all flex items-center gap-2 shadow-lg shadow-red-100"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 9h1a1 1 0 110 2H9V9z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 13h1a1 1 0 110 2H9v-2z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17h1a1 1 0 110 2H9v-2z" /></svg>
            PDF
          </button>
          <div class="w-px h-8 bg-gray-200 mx-2 hidden md:block"></div>
          <button 
            onclick={saveBatch}
            disabled={isSaving}
            class="px-6 py-2.5 bg-black text-white text-sm font-bold rounded-xl hover:bg-gray-800 transition-all flex items-center gap-2 disabled:opacity-50 shadow-lg"
          >
            {#if isSaving}
              <svg class="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              Guardando Lote...
            {:else}
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" /></svg>
              GUARDAR REGISTROS
            {/if}
          </button>
        </div>
      </div>

      <div class="overflow-x-auto bg-white rounded-2xl border border-gray-100 shadow-sm">
        <table class="w-full text-left text-sm min-w-[1200px]">
          <thead>
            {#if unidadMinera}
              <tr class="bg-scientific-600 text-white font-black text-xs uppercase tracking-widest text-center border-b border-scientific-700">
                <th colspan="9" class="px-6 py-4">
                  {unidadMinera}
                </th>
              </tr>
            {/if}
            <tr class="bg-gray-50/50 text-gray-400 font-bold text-[10px] uppercase tracking-widest border-b border-gray-100">
              <th class="px-6 py-4 text-center">N</th>
              <th class="px-6 py-4">Clasificación</th>
              <th class="px-6 py-4">Código de Basilea</th>
              <th class="px-6 py-4">Descripción</th>
              <th class="px-6 py-4 text-scientific-600">Material IA</th>
              <th class="px-6 py-4 text-right">Total en Toneladas</th>
              <th class="px-6 py-4">Proceso de tratamiento para valorización</th>
              <th class="px-6 py-4">Proceso de tratamiento para reclasificación a no peligroso</th>
              <th class="px-6 py-4 text-center">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            {#each records as rec, i}
              <tr class="group hover:bg-gray-50/50 transition-colors">
                <td class="px-6 py-4 text-center font-bold text-gray-900">{i + 1}</td>
                <td class="px-6 py-4 text-center">
                  <span class="px-2.5 py-1 rounded-full text-[10px] font-black uppercase {rec.tipo_residuo === 'PELIGROSO' ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}">
                    {rec.tipo_residuo}
                  </span>
                </td>
                <td class="px-6 py-4 text-center">
                  <div class="text-[10px] font-bold text-gray-700 bg-gray-50 inline-block px-1.5 rounded uppercase">{rec.codigo_basilea ?? 'N/A'}</div>
                </td>
                <td class="px-6 py-4">
                  <div class="font-medium text-gray-700">{rec.caracteristica ?? 'Sin descripción'}</div>
                  <div class="text-[9px] text-gray-400 uppercase mt-1 italic">{rec.razon_social ?? ''} {rec.planta ? `- ${rec.planta}` : ''}</div>
                </td>
                <td class="px-6 py-4">
                  <div class="font-black text-scientific-700 leading-tight uppercase text-xs">{rec.analysis_material_name || 'Pendiente'}</div>
                  <div class="flex gap-1 mt-1">
                    {#if rec._isCharacterizing}
                      <svg class="animate-spin h-3 w-3 text-scientific-500" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                      <span class="text-[9px] font-bold text-gray-400 uppercase tracking-tighter">Analizando...</span>
                    {:else}
                      <span class="w-2 h-2 rounded-full bg-scientific-400 animate-pulse"></span>
                      <span class="text-[9px] font-bold text-scientific-500 uppercase tracking-tighter">Caracterizado</span>
                    {/if}
                  </div>
                </td>
                <td class="px-6 py-4 text-right">
                  <div class="font-black text-gray-900">{(Number(rec.peso_total || 0) / 1000).toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 3 })}</div>
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
                      <div class="mt-2 text-right border-t border-amber-100 pt-1">
                        <span class="text-base font-black text-amber-600">{rec.viabilidad_reclasificacion || 0}%</span>
                        <span class="text-[8px] font-bold text-amber-400 uppercase tracking-tighter italic ml-1">Probabilidad</span>
                      </div>
                    </div>
                  {:else}
                    <span class="text-[10px] font-bold {rec.recla_no_peligroso === 'No aplica' ? 'text-green-500 bg-green-50' : 'text-gray-400 italic'} px-2 py-0.5 rounded">
                      {rec.recla_no_peligroso === 'No aplica' ? 'No requiere' : 'Cargando...'}
                    </span>
                  {/if}
                </td>
                <td class="px-6 py-4 text-center">
                  <button onclick={() => removeRecord(i)} class="p-2 text-gray-300 hover:text-red-500 transition-colors">
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
