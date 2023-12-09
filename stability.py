import os
import io
import warnings
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation

# Our Host URL should not be prepended with "https" nor should it have a trailing slash.
os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'

os.environ['STABILITY_KEY'] = 'sk-emY4uq5YaQf9gUxBHckZwSolw71JP4OTJcN5nqtgLbLHIhXW'

# Set up our connection to the API.
stability_api = client.StabilityInference(
    key=os.environ['STABILITY_KEY'],  # API Key reference.
    verbose=True,  # Print debug messages.
    # Set the engine to use for generation.
    engine="stable-diffusion-xl-beta-v2-2-2",
    #engine="stable-diffusion-512-v2-1",
    # Available engines: stable-diffusion-v1 stable-diffusion-v1-5 stable-diffusion-512-v2-0 stable-diffusion-768-v2-0
    # stable-diffusion-512-v2-1 stable-diffusion-768-v2-1 stable-diffusion-xl-beta-v2-2-2 stable-inpainting-v1-0 stable-inpainting-512-v2-0
)

# Set up our initial generation parameters.
pr = "A close-up view of a raw fish head, lit by natural light, in the context of a pet owner feeding their dog outdoors. Colorful and vibrant, the image captures a moment of companionship between a pet and their owner."

answers = stability_api.generate(
    safety=False,
    #guidance_preset=generation.GUIDANCE_PRESET_FAST_BLUE,
    prompt=pr,
    # If a seed is provided, the resulting generated image will be deterministic.
    # seed=992446758,
    # What this means is that as long as all generation parameters remain the same, you can always recall the same image simply by generating it again.
    # Note: This isn't quite the case for CLIP Guided generations, which we tackle in the CLIP Guidance documentation.
    # Amount of inference steps performed on image generation. Defaults to 30.
    steps=100,
    # Influences how strongly your generation is guided to match your prompt.
    cfg_scale=7.0,
    # Setting this value higher increases the strength in which it tries to match your prompt.
    # Defaults to 7.0 if not specified.
    width=512,  # Generation width, defaults to 512 if not included.
    height=512,  # Generation height, defaults to 512 if not included.
    samples=1,  # Number of images to generate, defaults to 1 if not included.
    # Choose which sampler we want to denoise our generation with.
    sampler=generation.SAMPLER_K_DPM_2

    # Defaults to k_dpmpp_2m if not specified. Clip Guidance only supports ancestral samplers.
    # (Available Samplers: ddim, plms, k_euler, k_euler_ancestral, k_heun, k_dpm_2, k_dpm_2_ancestral, k_dpmpp_2s_ancestral, k_lms, k_dpmpp_2m, k_dpmpp_sde)
)

# Set up our warning to print to the console if the adult content classifier is tripped.
# If adult content classifier is not tripped, save generated images.
for resp in answers:
    for artifact in resp.artifacts:
        # print(artifact)
        if artifact.finish_reason == generation.FILTER:
            warnings.warn(
                "Your request activated the API's safety filters and could not be processed."
                "Please modify the prompt and try again.")
        if artifact.type == generation.ARTIFACT_IMAGE:
            img = Image.open(io.BytesIO(artifact.binary))
            img.show()
            # Save our generated images with their seed number as the filename.
            # img.save(str(artifact.seed) + ".png")
