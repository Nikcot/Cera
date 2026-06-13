const esbuild = require('esbuild');
const fs = require('fs');
const path = require('path');

const isWatch = process.argv.includes('--watch');

async function build() {
    console.log('🔨 Сборка Цера Extension...\n');

    // Bundle offscreen.js with Transformers.js
    const ctx = await esbuild.context({
        entryPoints: ['src/offscreen.js'],
        bundle: true,
        outfile: 'offscreen.bundle.js',
        format: 'esm',
        platform: 'browser',
        target: ['chrome116'],
        minify: !isWatch,
        sourcemap: isWatch ? 'inline' : false,
        define: {
            'process.env.NODE_ENV': '"production"',
        },
        // Don't try to bundle WASM files
        loader: {
            '.wasm': 'file',
        },
    });

    if (isWatch) {
        await ctx.watch();
        console.log('👀 Watching for changes...');
    } else {
        await ctx.rebuild();
        await ctx.dispose();

        // Show bundle size
        const stats = fs.statSync('offscreen.bundle.js');
        const sizeMB = (stats.size / 1024 / 1024).toFixed(1);
        console.log(`  ✓ offscreen.bundle.js (${sizeMB} MB)`);
        console.log('\n✅ Сборка завершена!\n');
        console.log('Теперь загрузите расширение в Chrome:');
        console.log('  chrome://extensions/ → Загрузить распакованное → эту папку\n');
    }
}

build().catch((err) => {
    console.error('Ошибка сборки:', err);
    process.exit(1);
});
