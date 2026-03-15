export type PreviewAsset = {
  id: string;
  scene_id: string;
  file_name: string;
  relative_path: string;
  url: string;
  resolved_url: string | null;
  mime_type: string;
  prompt: string;
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
  previews: PreviewAsset[];
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
  created_at: string;
};

export type RenderJob = {
  id: string;
  status: string;
  logs: string[];
  output_asset_ids: string[];
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
  status: string;
  storyboard: Storyboard | null;
  render_job: RenderJob | null;
  outputs: OutputAsset[];
  created_at: string;
  updated_at: string;
};
