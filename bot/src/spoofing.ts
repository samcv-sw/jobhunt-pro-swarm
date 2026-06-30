export const injectWebGLSpoofer = `
    const getParameterProxy = new Proxy(WebGLRenderingContext.prototype.getParameter, {
        apply: function(target, thisArg, argumentsList) {
            const param = argumentsList[0];
            // UNMASKED_VENDOR_WEBGL
            if (param === 37445) {
                return 'Apple Inc.';
            }
            // UNMASKED_RENDERER_WEBGL
            if (param === 37446) {
                return 'Apple M3 Max';
            }
            return Reflect.apply(target, thisArg, argumentsList);
        }
    });
    WebGLRenderingContext.prototype.getParameter = getParameterProxy;

    // Optional: Canvas noise injection to spoof canvas fingerprinting
    const toDataURLProxy = new Proxy(HTMLCanvasElement.prototype.toDataURL, {
        apply: function(target, thisArg, argumentsList) {
            const context = thisArg.getContext('2d');
            if (context) {
                // Add micro-noise
                const shift = {
                    'r': Math.floor(Math.random() * 10) - 5,
                    'g': Math.floor(Math.random() * 10) - 5,
                    'b': Math.floor(Math.random() * 10) - 5,
                    'a': Math.floor(Math.random() * 10) - 5
                };
                const width = thisArg.width;
                const height = thisArg.height;
                if (width && height) {
                    const imageData = context.getImageData(0, 0, width, height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] = Math.min(255, Math.max(0, imageData.data[i] + shift.r));
                        imageData.data[i + 1] = Math.min(255, Math.max(0, imageData.data[i + 1] + shift.g));
                        imageData.data[i + 2] = Math.min(255, Math.max(0, imageData.data[i + 2] + shift.b));
                        imageData.data[i + 3] = Math.min(255, Math.max(0, imageData.data[i + 3] + shift.a));
                    }
                    context.putImageData(imageData, 0, 0);
                }
            }
            return Reflect.apply(target, thisArg, argumentsList);
        }
    });
    HTMLCanvasElement.prototype.toDataURL = toDataURLProxy;
`;
