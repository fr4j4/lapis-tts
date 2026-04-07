/**
 * LAPIS-TTS Plugin for OpenClaw
 * 
 * Integración con LAPIS-TTS para efectos de voz invisibles al usuario.
 * 
 * Características:
 * - Extrae bloques [[tts:text]]...[[/tts:text]]
 * - Transforma cues del modelo (whisper), (robotic), etc. a tags <whisper>, <robotic>
 * - Oculta bloques TTS al usuario (solo se escuchan, no se ven)
 * - Soporta modos: whisper, robotic, emphatic, dramatic, radio, breathy, intimate, menacing
 */

const https = require('https');
const http = require('http');
const { URL } = require('url');

function createLogger(label) {
  return {
    info: (...args) => console.log(`[${label}]`, ...args),
    error: (...args) => console.error(`[${label}]`, ...args),
    debug: (...args) => process.env.DEBUG && console.log(`[${label}]`, ...args)
  };
}

/**
 * Procesador de texto TTS
 */
class TtsTextProcessor {
  constructor() {
    this.cueToTagMap = {
      '(whisper)': '<whisper>',
      '(/whisper)': '</whisper>',
      '(whisper start)': '<whisper>',
      '(whisper end)': '</whisper>',
      '(robotic)': '<robotic>',
      '(/robotic)': '</robotic>',
      '(robot start)': '<robotic>',
      '(robot end)': '</robotic>',
      '(emphatic)': '<emphatic>',
      '(/emphatic)': '</emphatic>',
      '(dramatic)': '<dramatic>',
      '(/dramatic)': '</dramatic>',
      '(radio)': '<radio>',
      '(/radio)': '</radio>',
      '(phone)': '<radio>',
      '(/phone)': '</radio>',
      '(breathy)': '<breathy>',
      '(/breathy)': '</breathy>',
      '(intimate)': '<intimate>',
      '(/intimate)': '</intimate>',
      '(menacing)': '<menacing>',
      '(/menacing)': '</menacing>',
      '(threatening)': '<menacing>',
      '(/threatening)': '</menacing>',
    };
    
    this.ttsBlockRegex = /\[\[tts:text\]\]([\s\S]*?)\[\[\/tts:text\]\]/g;
    this.ttsDirectiveRegex = /\[\[tts:[^\]]+\]\]/g;
  }

  /**
   * Procesa el texto completo de la respuesta
   * Retorna: { visibleText, ttsText, hasTtsContent }
   */
  processResponse(text) {
    if (!text) return { visibleText: '', ttsText: '', hasTtsContent: false };
    
    let visibleText = text;
    let ttsText = '';
    let hasTtsContent = false;
    
    const ttsBlocks = [];
    let match;
    while ((match = this.ttsBlockRegex.exec(text)) !== null) {
      ttsBlocks.push({
        full: match[0],
        content: match[1].trim()
      });
    }
    
    if (ttsBlocks.length > 0) {
      hasTtsContent = true;
      
      const ttsParts = ttsBlocks.map(block => this.transformCuesToTags(block.content));
      ttsText = ttsParts.join(' ');
      
      visibleText = text.replace(this.ttsBlockRegex, '').trim();
      visibleText = visibleText.replace(/\s+/g, ' ');
    } else {
      ttsText = text.replace(this.ttsDirectiveRegex, '').trim();
      visibleText = text;
    }
    
    ttsText = ttsText.replace(this.ttsDirectiveRegex, '').trim();
    
    return { visibleText, ttsText, hasTtsContent };
  }

  /**
   * Transforma cues del modelo a tags de LAPIS
   */
  transformCuesToTags(text) {
    let result = text;
    
    for (const [cue, tag] of Object.entries(this.cueToTagMap)) {
      const escapedCue = cue.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(escapedCue, 'gi');
      result = result.replace(regex, tag);
    }
    
    result = this.sanitizeForTts(result);
    
    return result;
  }

  /**
   * Sanitiza texto para TTS
   */
  sanitizeForTts(text) {
    return text
      .replace(/[\u{1F600}-\u{1F64F}]/gu, '')
      .replace(/[\u{1F300}-\u{1F5FF}]/gu, '')
      .replace(/[\u{1F680}-\u{1F6FF}]/gu, '')
      .replace(/[\u{1F1E0}-\u{1F1FF}]/gu, '')
      .replace(/[\u{2600}-\u{26FF}]/gu, '')
      .replace(/[\u{2700}-\u{27BF}]/gu, '')
      .replace(/[\u{FE00}-\u{FE0F}]/gu, '')
      .replace(/[\u{1F3FB}-\u{1F3FF}]/gu, '')
      .replace(/[\u{1F900}-\u{1F9FF}]/gu, '')
      .replace(/[\u{1FA00}-\u{1FA6F}]/gu, '')
      .replace(/[\u{1FA70}-\u{1FAFF}]/gu, '')
      .trim();
  }
}

/**
 * LAPIS-TTS Speech Provider para OpenClaw
 */
function buildLapisSpeechProvider({ config, log }) {
  const baseUrl = config?.baseUrl || 'http://127.0.0.1:3000';
  const defaultVoice = config?.voice || 'robot-es';
  const timeoutMs = config?.timeoutMs || 30000;
  
  const processor = new TtsTextProcessor();
  
  log?.info?.(`LAPIS-TTS initialized: ${baseUrl}, voice: ${defaultVoice}`);

  return {
    id: "lapis",
    displayName: "LAPIS-TTS (Local)",
    autoSelectOrder: 1,
    
    isConfigured({ cfg, providerConfig }) {
      try {
        new URL('/v1/voices', providerConfig?.baseUrl || baseUrl);
        return true;
      } catch (err) {
        log?.error?.('Invalid baseUrl:', err.message);
        return false;
      }
    },

    resolveConfig({ cfg, rawConfig }) {
      return {
        baseUrl: rawConfig?.baseUrl || baseUrl,
        voice: rawConfig?.voice || defaultVoice,
        timeoutMs: rawConfig?.timeoutMs || timeoutMs,
      };
    },

    /**
     * Synthesize speech
     */
    async synthesize({ text, voice, cfg, providerConfig, ...otherParams }) {
      const effectiveBaseUrl = providerConfig?.baseUrl || baseUrl;
      const effectiveVoice = voice || providerConfig?.voice || defaultVoice;
      const effectiveTimeout = providerConfig?.timeoutMs || timeoutMs;
      
      log?.debug?.('Original text:', text?.substring(0, 100));
      
      const { visibleText, ttsText, hasTtsContent } = processor.processResponse(text);
      
      log?.debug?.('TTS text:', ttsText?.substring(0, 100));
      log?.debug?.('Visible text:', visibleText?.substring(0, 100));
      
      const textToSynthesize = ttsText || text;
      
      if (!textToSynthesize || textToSynthesize.trim().length === 0) {
        throw new Error('No text content for TTS after processing');
      }

      const url = new URL(`/v1/text-to-speech/${effectiveVoice}`, effectiveBaseUrl);
      
      const requestBody = JSON.stringify({
        text: textToSynthesize,
      });

      log?.debug?.('Requesting TTS from:', url.toString());

      return new Promise((resolve, reject) => {
        const client = url.protocol === 'https:' ? https : http;
        
        const req = client.request(
          url,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Content-Length': Buffer.byteLength(requestBody),
              'Accept': 'audio/wav'
            },
            timeout: effectiveTimeout
          },
          (res) => {
            if (res.statusCode !== 200) {
              let errorData = '';
              res.on('data', chunk => errorData += chunk);
              res.on('end', () => {
                log?.error?.(`LAPIS-TTS error ${res.statusCode}:`, errorData);
                reject(new Error(`LAPIS-TTS error ${res.statusCode}: ${errorData}`));
              });
              return;
            }

            const chunks = [];
            res.on('data', chunk => chunks.push(chunk));
            res.on('end', () => {
              const audioBuffer = Buffer.concat(chunks);
              
              if (audioBuffer.length < 1000) {
                log?.error?.('Empty or invalid audio received');
                reject(new Error('LAPIS-TTS returned empty or invalid audio'));
                return;
              }
              
              log?.info?.(`TTS generated: ${audioBuffer.length} bytes, voice: ${effectiveVoice}`);
              
              resolve({
                success: true,
                audioBuffer,
                fileExtension: '.wav',
                outputFormat: 'audio/wav',
                voiceCompatible: true,
                provider: 'lapis',
                metadata: {
                  voice: effectiveVoice,
                  hasTtsContent,
                  originalLength: text?.length,
                  ttsLength: ttsText?.length
                }
              });
            });
          }
        );

        req.on('error', (err) => {
          log?.error?.('Request failed:', err.message);
          reject(new Error(`LAPIS-TTS request failed: ${err.message}`));
        });

        req.on('timeout', () => {
          req.destroy();
          log?.error?.(`Request timeout after ${effectiveTimeout}ms`);
          reject(new Error(`LAPIS-TTS request timed out after ${effectiveTimeout}ms`));
        });

        req.write(requestBody);
        req.end();
      });
    },

    /**
     * List available voices from LAPIS
     */
    async listVoices({ cfg, providerConfig }) {
      const effectiveBaseUrl = providerConfig?.baseUrl || baseUrl;
      const effectiveTimeout = providerConfig?.timeoutMs || timeoutMs;
      
      return new Promise((resolve, reject) => {
        const url = new URL('/v1/voices', effectiveBaseUrl);
        const client = url.protocol === 'https:' ? https : http;
        
        log?.debug?.('Fetching voices from:', url.toString());
        
        const req = client.request(
          url,
          {
            method: 'GET',
            timeout: effectiveTimeout,
            headers: {
              'Accept': 'application/json'
            }
          },
          (res) => {
            if (res.statusCode !== 200) {
              reject(new Error(`Failed to list voices: ${res.statusCode}`));
              return;
            }

            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
              try {
                const response = JSON.parse(data);
                const voices = (response.voices || []).map(v => ({
                  id: v.voice_id,
                  name: v.name,
                  language: v.language || 'es',
                  description: v.description || ''
                }));
                log?.info?.(`Found ${voices.length} voices`);
                resolve(voices);
              } catch (err) {
                reject(new Error('Invalid response from LAPIS-TTS'));
              }
            });
          }
        );

        req.on('error', (err) => {
          reject(new Error(`Failed to list voices: ${err.message}`));
        });

        req.end();
      });
    }
  };
}

// Plugin entry point
module.exports = function activate(api) {
  const log = createLogger('lapis-tts');
  
  if (typeof api?.registerSpeechProvider !== 'function') {
    log.error('OpenClaw API does not support registerSpeechProvider');
    return;
  }
  
  const pluginConfig = api.config || {};
  
  log.info('Plugin config received:', JSON.stringify(pluginConfig));
  log.info('Activating LAPIS-TTS plugin v1.1.0');
  
  api.registerSpeechProvider(buildLapisSpeechProvider({
    config: pluginConfig,
    log
  }));
  
  log.info('LAPIS-TTS provider registered successfully');
};

module.exports.buildLapisSpeechProvider = buildLapisSpeechProvider;
