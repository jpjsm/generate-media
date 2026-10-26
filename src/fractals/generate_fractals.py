import numpy as np
import matplotlib.pyplot as plt
import turtle


def mandelbrot(w=800, h=600, max_iter=100):
    x = np.linspace(-2.5, 1, w)
    y = np.linspace(-1, 1, h)
    c = x[np.newaxis, :] + 1j * y[:, np.newaxis]
    z = np.zeros_like(c)
    n = np.zeros(c.shape, dtype=int)
    for i in range(max_iter):
        mask = np.abs(z) <= 2
        z[mask] = z[mask] ** 2 + c[mask]
        n[mask] = i
    return n


def koch(t, largo, nivel):
    if nivel == 0:
        t.forward(largo)
    else:
        for ang in (60, -120, 60, 0):
            koch(t, largo / 3, nivel - 1)
            t.left(ang)


if __name__ == "__main__":
    print("Generating mandelbrot fractal.")

    plt.imshow(mandelbrot(), cmap="magma", extent=(-2.5, 1, -1, 1))
    plt.axis("off")
    # plt.show()
    plt.savefig("./mandelbrot.png")
    print("Mandelbrot fractal generated.")

    print("Generating koch fractal.")
    t = turtle.Turtle()
    t.speed(0)
    for _ in range(3):
        koch(t, 300, 3)
        t.right(120)

    turtle.done()
