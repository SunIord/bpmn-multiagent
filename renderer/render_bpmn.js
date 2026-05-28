import fs from "fs";
import path from "path";
import puppeteer from "puppeteer";

const inputPath = process.argv[2];
const outputDir = process.argv[3];

if (!inputPath || !outputDir) {
    console.error("Uso:");
    console.error("node render_bpmn.js input.bpmn output_dir");
    process.exit(1);
}

const xml = fs.readFileSync(inputPath, "utf-8");

const fileName = path.basename(inputPath, ".bpmn");

const svgPath = path.join(outputDir, `${fileName}.svg`);
const pngPath = path.join(outputDir, `${fileName}.png`);

const browser = await puppeteer.launch({
    headless: true
});

const page = await browser.newPage();

await page.setViewport({
    width: 2200,
    height: 1400
});

await page.setContent(`
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">

    <style>
        html, body {
            margin: 0;
            padding: 0;
            background: white;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }

        #canvas {
            width: 100%;
            height: 100%;
        }
    </style>
</head>

<body>

<div id="canvas"></div>

<script type="module">

import BpmnViewer from 'https://cdn.jsdelivr.net/npm/bpmn-js@17.11.1/dist/bpmn-viewer.production.min.js';

const viewer = new BpmnViewer({
    container: '#canvas'
});

const xml = \`${xml.replace(/`/g, "\\`")}\`;

viewer.importXML(xml)
.then(() => {
    viewer.get('canvas').zoom('fit-viewport');

    window.renderComplete = true;
})
.catch(err => {
    console.error(err);
    window.renderError = err.toString();
});

</script>

</body>
</html>
`);

await page.waitForFunction(() => {
    return window.renderComplete === true || window.renderError;
}, {
    timeout: 15000
});

const error = await page.evaluate(() => window.renderError);

if (error) {
    console.error("Erro BPMN:", error);
    await browser.close();
    process.exit(1);
}

const svgContent = await page.$eval(
    "svg",
    el => el.outerHTML
);

fs.writeFileSync(svgPath, svgContent);

await page.screenshot({
    path: pngPath,
    fullPage: true
});

console.log("SVG salvo em:", svgPath);
console.log("PNG salvo em:", pngPath);

await browser.close();