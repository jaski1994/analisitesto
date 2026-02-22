import os
import ollama
from ollama import AsyncClient

class LLMManager:
    def __init__(self, use_docker=True):
        # Allow override via env var, default to internal docker service name and port 11434
        ollama_host = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
        
        if use_docker:
            # Inside Docker we must use the service name and INTERNAL port (11434)
            # The port 11435 is only for accessing from your host machine (outside docker)
            print(f"Connecting to Docker Ollama at: {ollama_host}")
            self.client = ollama.Client(host=ollama_host)
            self.async_client = AsyncClient(host=ollama_host)
        else:
            # Local Ollama (usually localhost:11434)
            print("Using Local Ollama")
            self.client = ollama.Client()
            self.async_client = AsyncClient()
        self.modelsSelected = ["llama3.2:3b","phi4-mini","qwen3:4b"]

    def get_available_models(self):
        """Equivalente di 'ollama list': modelli scaricati su disco."""
        models = self.client.list()
        available = []
        for m in models.get('models', []):
            available.append({
                'name': m.model,
                'size_gb': m.size / (1024**3),
                'modified_at': m.modified_at
            })
        return available
        
    def check_loaded_models(self):
        """Restituisce la lista dei modelli attualmente in RAM."""
        try:
            response = self.client.ps()
            loaded = []
            for model in response.get('models', []):
                loaded.append({
                    'name': model.model,
                    'size_vram': model['size_vram'] / (1024**3) # Converti in GB
                })
            return loaded
        except Exception as e:
            return f"Errore: {e}"

    def unload_model(self, model_name):
        """Scarica un modello specifico dalla RAM immediatamente."""
        try:
            # In Ollama, impostare keep_alive a 0 scarica il modello
            self.client.generate(model=model_name, keep_alive=0)
            return f"Modello {model_name} scaricato con successo."
        except Exception as e:
            return f"Errore durante lo scaricamento: {e}"

    def auto_cleanup(self, ram_threshold_percent=90):
        """Scarica tutti i modelli se la RAM del sistema è quasi piena."""
        ram_usage = psutil.virtual_memory().percent
        if ram_usage > ram_threshold_percent:
            loaded = self.check_loaded_models()
            for m in loaded:
                self.unload_model(m['name'])
            return "RAM critica! Tutti i modelli sono stati scaricati."
        return f"RAM OK: {ram_usage}%"

    def get_status_ram_vram(self):
        """Equivalente di 'ollama ps': modelli in esecuzione e dove si trovano."""
        status = self.client.ps()
        active = []
        for m in status.get('models', []):
            total_size = m['size']
            vram_size = m['size_vram']
            
            # Calcolo della distribuzione
            gpu_percent = (vram_size / total_size) * 100 if total_size > 0 else 0
            
            active.append({
                'name': m['name'],
                'in_vram_gb': vram_size / (1024**3),
                'total_gb': total_size / (1024**3),
                'location': "GPU/VRAM" if gpu_percent == 100 else f"Ibrido ({gpu_percent:.1f}% GPU)"
            })
        return active
        
    def load_model(self, model_name):
        """Carica il modello in RAM/VRAM senza generare testo."""
        try:
            # Inviando una richiesta di generazione vuota con keep_alive, 
            # Ollama carica il modello e lo mantiene pronto.
            self.client.generate(model=model_name, prompt='', keep_alive='5m')
            return True
        except Exception as e:
            print(f"Errore caricamento: {e}")
            return False


    async def call_the_llm(self, model="llama3.2:3b", prompt="", options={}):
       
        try:
            response = await self.async_client.generate(
                model=model,
                prompt=prompt,
                stream=False,
                options=options
            )
            
            return response
        
        except Exception as e:
            return str(e)

    async def pull_model_async(self, model_name: str):
        """
        Async pull model.
        """
        try:
            stream = await self.async_client.pull(model_name, stream=True)

            print(f"Pulling model: {model_name}")

            async for chunk in stream:
                status = chunk.get("status", "")
                completed = chunk.get("completed", 0)
                total = chunk.get("total", 0)

            if total > 0:
                percent = (completed / total) * 100
                print(f"\r{status} - {percent:.1f}%", end="")

            else:
                print(f"\r{status}", end="")

            print("\nDownload complete.")
            return True


        except Exception as e:
            print(f"Async pull error: {e}")
            return False

    def pull_model_thread(self, model_name):
        """Streaming sync pull in a background thread with cache-based progress tracking."""
        import threading
        from django.core.cache import cache

        cache_key = f"ollama_pull_{model_name.replace(':', '_')}"

        def run_pull():
            print(f"Starting background pull for {model_name}...")
            cache.set(cache_key, {"progress": 0, "status": "starting", "completed": 0, "total": 0}, timeout=3600)
            try:
                for chunk in self.client.pull(model_name, stream=True):
                    status = getattr(chunk, 'status', '') or ''
                    completed = getattr(chunk, 'completed', 0) or 0
                    total = getattr(chunk, 'total', 0) or 0
                    percent = round((completed / total) * 100, 1) if total > 0 else 0
                    cache.set(cache_key, {
                        "progress": percent,
                        "status": status,
                        "completed": completed,
                        "total": total,
                    }, timeout=3600)

                # Mark as done
                cache.set(cache_key, {"progress": 100, "status": "success", "completed": 0, "total": 0}, timeout=60)
                print(f"Successfully pulled {model_name}")
            except Exception as e:
                cache.set(cache_key, {"progress": -1, "status": f"error: {e}", "completed": 0, "total": 0}, timeout=300)
                print(f"Failed to pull {model_name}: {e}")

        thread = threading.Thread(target=run_pull, daemon=True)
        thread.start()
        return True





# --- Utilizzo ---
# manager = LLMManager()
# # 1
# print("--- MODELLI DISPONIBILI (SU DISCO) ---")
# for m in manager.get_available_models():
#     print(f"- {m['name']} ({m['size_gb']:.2f} GB)")
# 
# # 2
# print("\n--- STATO MEMORIA (RAM vs VRAM) ---")
# attivi = manager.get_status_ram_vram()
# if not attivi:
#     print("Nessun modello caricato al momento.")
# else:
#     for a in attivi:
#         print(f"- {a['name']}: {a['location']}")
# 
# # 3
# print("Modelli caricati:", manager.check_loaded_models())
# 
# # 4
# print(manager.unload_model("phi3.5"))