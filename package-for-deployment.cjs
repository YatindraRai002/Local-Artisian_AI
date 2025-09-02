const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🚀 Packaging Hindi NLP Platform for Deployment...');

// Ensure build exists
console.log('📦 Building project...');
try {
    execSync('npm run build', { stdio: 'inherit' });
} catch (error) {
    console.error('Build failed:', error.message);
    process.exit(1);
}

// Copy important files to dist for complete deployment package
const filesToCopy = [
    'vercel.json',
    'package.json',
    'deploy.md',
    'test-hindi-nlp.html',
    'test-api.html'
];

console.log('📋 Copying configuration files...');

filesToCopy.forEach(file => {
    if (fs.existsSync(file)) {
        fs.copyFileSync(file, path.join('dist', file));
        console.log(`✅ Copied ${file}`);
    } else {
        console.log(`⚠️  ${file} not found, skipping`);
    }
});

// Copy API directory
if (fs.existsSync('api')) {
    const apiDest = path.join('dist', 'api');
    if (!fs.existsSync(apiDest)) {
        fs.mkdirSync(apiDest, { recursive: true });
    }
    
    const apiFiles = fs.readdirSync('api');
    apiFiles.forEach(file => {
        fs.copyFileSync(path.join('api', file), path.join(apiDest, file));
        console.log(`✅ Copied api/${file}`);
    });
}

// Copy public directory (CSV data)
if (fs.existsSync('public')) {
    const publicDest = path.join('dist', 'public');
    if (!fs.existsSync(publicDest)) {
        fs.mkdirSync(publicDest, { recursive: true });
    }
    
    const publicFiles = fs.readdirSync('public');
    publicFiles.forEach(file => {
        fs.copyFileSync(path.join('public', file), path.join(publicDest, file));
        console.log(`✅ Copied public/${file}`);
    });
}

// Create deployment info
const deployInfo = {
    name: 'Kala-Kaart Hindi NLP Platform',
    version: '2.0.0',
    description: 'Traditional Indian Artisan Discovery Platform with Hindi NLP',
    features: [
        'Hindi Language Processing',
        'Bilingual Chat Interface',
        'Traditional Craft Database',
        'Real-time Search',
        'Cultural Context Understanding'
    ],
    nlp_pipeline: [
        'Text Preprocessing',
        'Hindi Tokenization',
        'Vector Embeddings',
        'Encoder-Decoder Translation',
        'Intent Classification',
        'Response Generation'
    ],
    deployment_ready: true,
    build_date: new Date().toISOString(),
    instructions: 'Upload the entire dist folder to any hosting platform'
};

fs.writeFileSync(path.join('dist', 'deployment-info.json'), JSON.stringify(deployInfo, null, 2));

console.log('\n🎉 Deployment package ready!');
console.log('\n📁 Your complete deployment package is in the "dist" folder');
console.log('\n🌐 To deploy:');
console.log('   1. Upload entire "dist" folder to any hosting service');
console.log('   2. Or use: vercel deploy dist --prod');
console.log('   3. Or drag "dist" folder to netlify.com');
console.log('\n✨ Your Hindi NLP platform is ready to go live!');

// Display file count
const distFiles = getAllFiles('dist');
console.log(`\n📊 Package contains ${distFiles.length} files total`);

function getAllFiles(dir) {
    let files = [];
    const items = fs.readdirSync(dir);
    
    items.forEach(item => {
        const fullPath = path.join(dir, item);
        if (fs.statSync(fullPath).isDirectory()) {
            files = files.concat(getAllFiles(fullPath));
        } else {
            files.push(fullPath);
        }
    });
    
    return files;
}