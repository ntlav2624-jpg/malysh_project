import numpy as np
import matplotlib.pyplot as plt

N_modes = 100
time_steps = 50
np.random.seed(42)
phases = np.random.uniform(0, 2 * np.pi, N_modes)
coupling_strength = 0.35

mean_phase_diffs = []

for t in range(time_steps):
    diffs = np.abs(np.diff(phases))
    mean_diff = np.mean(diffs)
    mean_phase_diffs.append(mean_diff)
    
    new_phases = phases.copy()
    for i in range(1, N_modes - 1):
        delta = coupling_strength * (np.sin(phases[i+1] - phases[i]) + np.sin(phases[i-1] - phases[i]))
        new_phases[i] += delta
    phases = new_phases

plt.figure(figsize=(10, 6), facecolor='#1e1e1e')
ax = plt.axes()
ax.set_facecolor('#1e1e1e')

plt.plot(range(time_steps), mean_phase_diffs, 'c-', linewidth=3, label='Средняя разность фаз модовых осцилляторов')
plt.axhline(y=np.pi/2, color='yellow', linestyle='--', label='Порог резонансного сопряжения')

plt.title('Динамика фазового зацепления через оператор R (Модель «Малыш»)', color='white', fontsize=14, fontweight='bold')
plt.xlabel('Шаг симуляции (t)', color='white', fontsize=12)
plt.ylabel('Разность фаз (рад)', color='white', fontsize=12)

legend = plt.legend(loc='upper right', facecolor='#2d2d2d', edgecolor='none')
for text in legend.get_texts():
    text.set_color('white')

plt.grid(True, color='#444444', linestyle='--', alpha=0.5)
plt.tick_params(colors='white', which='both')
for spine in ax.spines.values():
    spine.set_color('#666666')

plt.tight_layout()
plt.savefig('phase_entanglement.png', dpi=300, facecolor='#1e1e1e')
print("График фазового зацепления успешно сохранен как phase_entanglement.png")
