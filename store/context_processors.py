def cart_context(request):
    cart = request.session.get('cart', {})
    cart_count = 0

    for item in cart.values():
        if isinstance(item, dict):
            cart_count += int(item.get('quantity', 0))
        else:
            try:
                cart_count += int(item)
            except (ValueError, TypeError):
                continue

    return {
        'cart_count': cart_count
    }