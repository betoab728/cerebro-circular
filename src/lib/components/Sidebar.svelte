<script lang="ts">
  import { page } from '$app/stores';
  
  const menuItems = [
    { name: 'Dashboard', href: '/dashboard', icon: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' },
    { name: 'Registros Maestros', href: '/registry', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' },
    { name: 'Selección Inteligente', href: '/analysis', icon: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z' },
  ];
</script>

<aside class="w-64 bg-white border-r border-gray-200 h-screen fixed left-0 top-0 hidden md:flex flex-col z-10">
  <div class="h-16 flex items-center px-6 border-b border-gray-100">
    <div class="flex items-center gap-2">
      <img src="/logoazul.png" alt="Logo" class="w-12 h-12 object-contain" />
      <span class="text-base font-bold text-gray-800 tracking-tight">CEREBRO CIRCULAR</span>
    </div>
  </div>

  <nav class="p-4 space-y-1 overflow-y-auto flex-1">
    {#each menuItems as item}
      {@const isActive = $page.url.pathname.startsWith(item.href)}
      <a 
        href={item.href}
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-200
        {isActive ? 'bg-scientific-50 text-scientific-700' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}">
        <svg class="w-5 h-5 flex-shrink-0 {isActive ? 'text-scientific-600' : 'text-gray-400'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={item.icon} />
        </svg>
        {item.name}
      </a>
    {/each}
  </nav>

  <div class="p-4 border-t border-gray-100">
    <div class="flex items-center gap-3 px-3 py-2">
      <div class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-xs font-medium text-gray-500">
        IA
      </div>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-gray-900 truncate">Ing. Ambiental</p>
        <p class="text-xs text-gray-500 truncate">Admin</p>
      </div>
    </div>
  </div>
</aside>
