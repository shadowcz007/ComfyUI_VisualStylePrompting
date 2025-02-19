import comfy
import torch
import nodes

from .utils.attention_functions import VisualStyleProcessor

class ApplyVisualStyle:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "vae": ("VAE", ),
                "reference_image": ("IMAGE",),
                "conditioning_prompt": ("CONDITIONING",),
                "reference_image_prompt": ("CONDITIONING",),
                "negative_prompt": ("CONDITIONING", ),
                "enabled": ("BOOLEAN", {"default": True}),
                "denoise": ("FLOAT", {"default": 1., "min": 0., "max": 1., "step": 1e-2})
            }
        }

    RETURN_TYPES = ("MODEL", "CONDITIONING","CONDITIONING", "LATENT")
    RETURN_NAMES = ("model", "positive", "negative", "latents")
    
    FUNCTION = "apply_visual_style_prompt"

    def apply_visual_style_prompt(
        self, 
        model: comfy.model_patcher.ModelPatcher, 
        vae,
        reference_image, 
        conditioning_prompt, 
        reference_image_prompt,
        negative_prompt, 
        enabled,
        denoise
    ):
        self.model = model
        reference_latent = vae.encode(reference_image[:,:,:,:3])
        
        for n, m in model.model.diffusion_model.named_modules():
            if m.__class__.__name__  == "CrossAttention":
                processor = VisualStyleProcessor(m, enabled=enabled)
                setattr(m, 'forward', processor.visual_style_forward)

        conditioning_prompt = reference_image_prompt + conditioning_prompt
        negative_prompt = negative_prompt * 2 

        latents = torch.zeros_like(reference_latent) 
        latents = torch.cat([latents] * 2)

        if denoise < 1.0:
            latents[::1] = reference_latent[:1]
        else:
            latents[::2] = reference_latent

        denoise_mask = torch.ones_like(latents)[:, :1, ...] * denoise

        denoise_mask[0] = 0.

        return (model, conditioning_prompt, negative_prompt, {"samples": latents, "noise_mask": denoise_mask})    

NODE_CLASS_MAPPINGS = {"ApplyVisualStyle": ApplyVisualStyle}

NODE_DISPLAY_NAME_MAPPINGS = {"ApplyVisualStyle": "Apply Visual Style Prompting"}
