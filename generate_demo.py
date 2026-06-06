import sys
import os
import urllib.request
import subprocess

sys.path.append('src')
from diff.compute import compute_diff
from graph.reducer import reduce_graph
from render.puml_renderer import render_puml
from domain.models import UMLClass, UMLAttribute, UMLMethod, UMLModel, UMLRelation

os.makedirs('docs', exist_ok=True)

base_model = UMLModel(
    module_name="demo_module",
    classes=(
        UMLClass(
            name="com.ecommerce.order.OrderService", kind="class", attributes=(
                UMLAttribute(name="db", type="Database", visibility="-"),
            ), methods=(
                UMLMethod(name="createOrder", return_type="Order", visibility="+", parameters=("Cart c",)),
                UMLMethod(name="cancelOrder", return_type="void", visibility="+", parameters=("String id",)),
            )
        ),
        UMLClass(
            name="com.ecommerce.order.Order", kind="class", attributes=(
                UMLAttribute(name="id", type="String", visibility="+"),
                UMLAttribute(name="total", type="double", visibility="+"),
            )
        ),
        UMLClass(
            name="com.ecommerce.payment.PaymentGateway", kind="interface", methods=(
                UMLMethod(name="charge", return_type="boolean", visibility="+", parameters=("double amount",)),
            )
        ),
        UMLClass(
            name="org.external.Logger", kind="class", methods=(
                UMLMethod(name="log", return_type="void", visibility="+", parameters=("String msg",)),
            )
        )
    ),
    relations=(
        UMLRelation(source="com.ecommerce.order.OrderService", target="com.ecommerce.order.Order", relation_type="association"),
        UMLRelation(source="com.ecommerce.order.OrderService", target="com.ecommerce.payment.PaymentGateway", relation_type="association"),
        UMLRelation(source="com.ecommerce.order.OrderService", target="org.external.Logger", relation_type="association"),
    )
)

pr_model = UMLModel(
    module_name="demo_module",
    classes=(
        UMLClass(
            # MOVED AND RENAMED from order.OrderService to checkout.CheckoutService
            name="com.ecommerce.checkout.CheckoutService", kind="class", attributes=(
                UMLAttribute(name="db", type="Database", visibility="-"),
                UMLAttribute(name="stripeClient", type="Stripe", visibility="-"), # NEW ATTRIBUTE
            ), methods=(
                UMLMethod(name="createOrder", return_type="Order", visibility="+", parameters=("Cart c",)),
                UMLMethod(name="createOrder", return_type="Order", visibility="+", parameters=("Cart c", "boolean fastTrack")), # OVERLOADED METHOD
            ) # Removed cancelOrder
        ),
        UMLClass(
            name="com.ecommerce.order.Order", kind="class", attributes=(
                UMLAttribute(name="id", type="String", visibility="+"),
                UMLAttribute(name="total", type="double", visibility="+"),
            )
        ),
        UMLClass(
            name="com.ecommerce.payment.PaymentGateway", kind="interface", methods=(
                UMLMethod(name="charge", return_type="boolean", visibility="+", parameters=("double amount",)),
            )
        ),
        UMLClass(
            name="org.external.Logger", kind="class", methods=(
                UMLMethod(name="log", return_type="void", visibility="+", parameters=("String msg",)),
            )
        )
    ),
    relations=(
        UMLRelation(source="com.ecommerce.checkout.CheckoutService", target="com.ecommerce.order.Order", relation_type="association"),
        UMLRelation(source="com.ecommerce.checkout.CheckoutService", target="com.ecommerce.payment.PaymentGateway", relation_type="association"),
        UMLRelation(source="com.ecommerce.checkout.CheckoutService", target="org.external.Logger", relation_type="association"),
    )
)

diff = compute_diff(base_model, pr_model)
spec = reduce_graph(base_model, pr_model, diff, context_depth=1)
puml_text = render_puml(base_model, pr_model, diff, spec)

with open("docs/demo.puml", "w", encoding="utf-8") as f:
    f.write(puml_text)

if not os.path.exists("plantuml.jar"):
    print("Downloading plantuml.jar...")
    urllib.request.urlretrieve("https://github.com/plantuml/plantuml/releases/download/v1.2024.4/plantuml-1.2024.4.jar", "plantuml.jar")

print("Rendering docs/demo.png...")
subprocess.run(["java", "-jar", "plantuml.jar", "docs/demo.puml", "-tpng"])
print("Generated docs/demo.png!")
