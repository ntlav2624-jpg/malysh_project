import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class MalyshVortexVisualizer:
    def __init__(self, resolution: int = 30):
        self.res = resolution
        x = np.linspace(-3.0, 3.0, self.res)
        y = np.linspace(-3.0, 3.0, self.res)
        z = np.linspace(-3.0, 3.0, self.res)
        self.X, self.Y, self.Z = np.meshgrid(x, y, z, indexing='ij')

    def compute_clebsch_potentials(self):
        alpha = self.X**2 + self.Y**2 - 1.0
        beta = self.Z + np.sin(self.X * self.Y)
        return alpha, beta

    def compute_vorticity_field(self, alpha, beta):
        dx = self.X[1, 0, 0] - self.X[0, 0, 0]
        
        grad_alpha = np.gradient(alpha, dx, dx, dx, axis=(0, 1, 2))
        grad_beta = np.gradient(beta, dx, dx, dx, axis=(0, 1, 2))
        
        omega_x = grad_alpha[1] * grad_beta[2] - grad_alpha[2] * grad_beta[1]
        omega_y = grad_alpha[2] * grad_beta[0] - grad_alpha[0] * grad_beta[2]
        omega_z = grad_alpha[0] * grad_beta[1] - grad_alpha[1] * grad_beta[0]
        
        omega_magnitude = np.sqrt(omega_x**2 + omega_y**2 + omega_z**2)
        return omega_magnitude

    def render_3d_vortex_plot(self):
        alpha, beta = self.compute_clebsch_potentials()
        omega_mag = self.compute_vorticity_field(alpha, beta)

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        vortex_core_mask = (omega_mag > np.percentile(omega_mag, 85))

        x_core = self.X[vortex_core_mask]
        y_core = self.Y[vortex_core_mask]
        z_core = self.Z[vortex_core_mask]
        intensity = omega_mag[vortex_core_mask]

        sc = ax.scatter(x_core, y_core, z_core, c=intensity, cmap='plasma', s=15, alpha=0.8)
        
        fig.colorbar(sc, ax=ax, shrink=0.6, label='Vorticity Magnitude')
        ax.set_title("Malysh: 3D Clebsch Vortex Intersection", fontsize=10)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")

        plt.savefig("malysh_vortex_3d.png", dpi=300)
        print("[VISUALIZATION] 3D vortex plot successfully generated and saved to 'malysh_vortex_3d.png'.")

if __name__ == "__main__":
    visualizer = MalyshVortexVisualizer(resolution=35)
    visualizer.render_3d_vortex_plot()
