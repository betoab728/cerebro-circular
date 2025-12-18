<script lang="ts">
	import Sidebar from '$lib/components/Sidebar.svelte';
	import "../../app.css";
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="min-h-screen bg-gray-50 flex">
	<Sidebar />
	<main class="flex-1 md:ml-64 min-h-screen flex flex-col transition-all duration-300 w-full">
		{@render children()}
	</main>
</div>
