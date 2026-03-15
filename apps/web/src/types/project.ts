export type PreviewAsset = {
  id: string;
  scene_id: string;
  file_name: string;
  relative_path: string;
  url: string;
  resolved_url: string | null;
  mime_type: string;
  prompt: string;
  source_prompt: string | null;
  positive_prompt: string | null;
  negative_prompt: string | null;
  consistency_notes: string | null;
  identity_constraints: string | null;
  camera_notes: string | null;
  lens_notes: string | null;
  lighting_notes: string | null;
  wardrobe_notes: string | null;
  mood_notes: string | null;
  background_notes: string | null;
  style_notes: string | null;
  configured_backend: string;
  generation_backend: string;
  generation_mode: string;
  variant_index: number;
  seed: number | null;
  model_name: string | null;
  retry_count: number;
  fallback_reason: string | null;
  prompt_signature: string | null;
  generation_duration_ms: number | null;
  identity_strength_score: number | null;
  identity_strength_label: string | null;
  identity_strength_reason: string | null;
  status: string;
  created_at: string;
};

export type IdentityImageAsset = {
  id: string;
  file_name: string;
  relative_path: string;
  url: string;
  resolved_url: string | null;
  mime_type: string;
  size_bytes: number;
  role: "primary" | "reference";
  created_at: string;
};

export type IdentityPack = {
  primary_image: IdentityImageAsset | null;
  reference_images: IdentityImageAsset[];
  character_notes: string | null;
  lock_identity: boolean;
  created_at: string;
  updated_at: string;
};

export type Scene = {
  id: string;
  title: string;
  beat: string;
  visual_prompt: string;
  negative_prompt: string;
  voiceover: string;
  duration_seconds: number;
  selected: boolean;
  selected_preview_id: string | null;
  preview_revision: number;
  preview_history_note: string | null;
  last_previews_generated_at: string | null;
  previews: PreviewAsset[];
  generated_video: OutputAsset | null;
};

export type Storyboard = {
  refined_title: string;
  script: string;
  overview: string;
  generated_at: string;
  scenes: Scene[];
};

export type OutputAsset = {
  id: string;
  file_name: string;
  relative_path: string;
  url: string;
  resolved_url: string | null;
  mime_type: string;
  summary: string;
  video_backend: string;
  video_generation_mode: string;
  provider_request_id: string | null;
  provider_status: string | null;
  provider_model_name: string | null;
  source_mode: string | null;
  duration_seconds: number | null;
  aspect_ratio: string | null;
  resolution: string | null;
  prompt_used: string | null;
  identity_mode: string | null;
  fallback_message: string | null;
  provider_asset_url: string | null;
  created_at: string;
  updated_at: string | null;
};

export type RenderJob = {
  id: string;
  status: string;
  logs: string[];
  output_asset_ids: string[];
  started_at: string | null;
  completed_at: string | null;
};

export type VideoJob = {
  id: string;
  status: string;
  target_type: string;
  target_id: string;
  backend: string;
  active_backend: string;
  generation_mode: string;
  provider_request_id: string | null;
  provider_status: string | null;
  logs: string[];
  output_asset_id: string | null;
  fallback_message: string | null;
  started_at: string | null;
  completed_at: string | null;
};

export type Project = {
  id: string;
  title: string;
  prompt: string;
  style: string;
  duration_target: number;
  aspect_ratio: "9:16" | "16:9";
  avatar_notes: string | null;
  identity_pack: IdentityPack | null;
  preview_backend: string;
  preview_backend_effective: string;
  preview_generation_mode: string;
  preview_backend_message: string | null;
  preview_model_name: string | null;
  preview_last_generated_at: string | null;
  video_backend: string;
  video_backend_effective: string;
  video_generation_mode: string;
  video_backend_message: string | null;
  video_model_name: string | null;
  video_last_generated_at: string | null;
  status: string;
  storyboard: Storyboard | null;
  render_job: RenderJob | null;
  video_job: VideoJob | null;
  project_video: OutputAsset | null;
  outputs: OutputAsset[];
  created_at: string;
  updated_at: string;
};
