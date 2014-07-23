jQuery( document ).fn.xpathEvaluate = function (xpathExpression)
{
   // NOTE: vars not declared local for debug purposes
   $this = this.first(); // Don't make me deal with multiples before coffee

   // Evaluate xpath and retrieve matching nodes
   xpathResult = this[0].evaluate(xpathExpression, this[0], null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);

   result = [];
   while (elem = xpathResult.iterateNext())
   {
      result.push(elem);
   }

   $result = jQuery( [] ).pushStack( result );
   return $result;
}