import ollama

class LLMManager:
    def __init__(self):
        self.client = ollama.Client()
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

# --- Utilizzo ---
manager = LLMManager()
# 1
print("--- MODELLI DISPONIBILI (SU DISCO) ---")
for m in manager.get_available_models():
    print(f"- {m['name']} ({m['size_gb']:.2f} GB)")

# 2
print("\n--- STATO MEMORIA (RAM vs VRAM) ---")
attivi = manager.get_status_ram_vram()
if not attivi:
    print("Nessun modello caricato al momento.")
else:
    for a in attivi:
        print(f"- {a['name']}: {a['location']}")

# 3
print("Modelli caricati:", manager.check_loaded_models())

# 4
print(manager.unload_model("phi3.5"))