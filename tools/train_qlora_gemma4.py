#!/usr/bin/env python3
"""
tools/train_qlora_gemma4.py
===========================
End-to-end QLoRA fine-tuning pipeline for Gemma 4 (31B QAT W4A16 CT)
tailored for Kaggle's 4x L4 GPU accelerator environment.

Trains a PEFT LoRA adapter (r=16, alpha=32) on SWE-bench issue-to-patch pairs
and exports the final weights to adapters/main_lora/adapter_model.safetensors.

Usage:
  python tools/train_qlora_gemma4.py \
    --model_path /kaggle/input/models/google/gemma-4/other/gemma-4-31b-it-qat-w4a16-ct/2 \
    --data_path data/expanded_benchmark_32.jsonl \
    --output_dir adapters/main_lora \
    --epochs 2
"""

import os
import sys
import json
import argparse
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune Gemma 4 LoRA adapter for SWE agent.")
    parser.add_argument("--model_path", type=str, default="gemma-4-31b-it-qat-w4a16-ct",
                        help="Path to mounted Gemma 4 checkpoint or Hugging Face ID")
    parser.add_argument("--data_path", type=str, default="data/expanded_benchmark_32.jsonl",
                        help="Path to training task JSONL file")
    parser.add_argument("--output_dir", type=str, default="adapters/main_lora",
                        help="Directory to save PEFT adapter weights")
    parser.add_argument("--epochs", type=int, default=2, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=1, help="Per-device batch size")
    parser.add_argument("--grad_accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--lora_r", type=int, default=16, help="LoRA rank")
    parser.add_argument("--lora_alpha", type=int, default=32, help="LoRA alpha")
    return parser.parse_args()

def load_swe_dataset(data_path: Path):
    tasks = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    print(f"Loaded {len(tasks)} training pairs from {data_path}")
    return tasks

def format_training_example(task: dict) -> list:
    task_id = task.get("task_id", "")
    issue = task.get("issue", "")
    test_cmd = task.get("test_cmd", "")
    patch = task.get("patch", "")
    
    user_prompt = (
        f"Task: {task_id}\n"
        f"Issue Description:\n{issue}\n\n"
        f"Validation Test:\n{test_cmd}\n\n"
        f"Diagnose the defect, formulate a minimal surgical fix, and execute submit_patch."
    )
    
    assistant_reply = (
        f"### Diagnostic Manifesto\n"
        f"- Target Issue: {task_id}\n"
        f"- Recommended Action: Apply surgical minimal diff and verify.\n\n"
        f"```diff\n{patch}\n```\n\n"
        f"<action>{{\"name\": \"submit_patch\", \"arguments\": {{}}}}</action>"
    )
    
    return [
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": assistant_reply}
    ]

def train():
    args = parse_args()
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("GEMMA 4 QLORA FINE-TUNING PIPELINE")
    print(f"  Model Path : {args.model_path}")
    print(f"  Data Path  : {args.data_path}")
    print(f"  Output Dir : {output_path}")
    print(f"  LoRA Config: r={args.lora_r}, alpha={args.lora_alpha}")
    print("=" * 60)
    
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
        from peft import LoraConfig, get_peft_model, TaskType
    except ImportError as e:
        print(f"[ERROR] Missing ML dependencies: {e}")
        print("Run this script in an environment with PyTorch, transformers, and peft installed.")
        sys.exit(1)
        
    print("[1/4] Loading Tokenizer and Base Model...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        local_files_only=True
    )
    
    print("[2/4] Initializing LoRA Adapter Layers...")
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    print("[3/4] Preparing Dataset...")
    raw_tasks = load_swe_dataset(Path(args.data_path))
    formatted_data = [format_training_example(t) for t in raw_tasks]
    
    # Tokenize training dialogues
    tokenized_inputs = []
    for dialog in formatted_data:
        text = tokenizer.apply_chat_template(dialog, tokenize=False)
        enc = tokenizer(text, truncation=True, max_length=4096, return_tensors="pt")
        tokenized_inputs.append({
            "input_ids": enc["input_ids"][0],
            "attention_mask": enc["attention_mask"][0],
            "labels": enc["input_ids"][0].clone()
        })
        
    training_args = TrainingArguments(
        output_dir=str(output_path / "checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        bf16=torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
        logging_steps=5,
        save_strategy="no",
        report_to="none"
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_inputs,
    )
    
    print("[4/4] Starting LoRA Fine-Tuning...")
    trainer.train()
    
    print(f"Saving fine-tuned LoRA weights to {output_path}...")
    model.save_pretrained(str(output_path))
    tokenizer.save_pretrained(str(output_path))
    print("[SUCCESS] LoRA adapter successfully fine-tuned and exported!")

if __name__ == "__main__":
    train()
