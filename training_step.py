import jax

import jax.numpy as jnp

from loss import get_compute_loss_lambda


def get_training_step_lambda(text_encoder, vae, unet):
    def __training_step_lambda(
        state,
        text_encoder_params,
        vae_params,
        batch,
        rng,
    ):

        sample_rng, new_rng = jax.random.split(rng, 2)

        jax_value_and_grad_loss = jax.value_and_grad(
            get_compute_loss_lambda(
                text_encoder,
                text_encoder_params,
                vae,
                vae_params,
                unet,
                state,
            )
        )

        loss, grad = jax_value_and_grad_loss(
            batch,
            sample_rng,
        )

        grad_mean = jax.lax.pmean(grad, "batch")

        new_state = state.apply_gradients(grads=grad_mean)

        metrics = jax.lax.pmean({"loss": loss}, axis_name="batch")

        l2_grads = jnp.sqrt(
            sum(
                [
                    jnp.vdot(x, x)
                    for x in jax.tree_util.tree_leaves(jax.tree_util.tree_leaves(grad))
                ]
            )
        )
        metrics["l2_grads"] = l2_grads

        return new_state, new_rng, metrics

    return __training_step_lambda
