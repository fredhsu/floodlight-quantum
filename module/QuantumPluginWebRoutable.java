package net.floodlightcontroller.quantumplugin;

import net.floodlightcontroller.restserver.RestletRoutable;

import org.restlet.Context;
import org.restlet.Restlet;
import org.restlet.routing.Router;

public class QuantumPluginWebRoutable implements RestletRoutable {

	@Override
	public Restlet getRestlet(Context context) {
	      Router router = new Router(context);
	        router.attach("/json", QuantumPluginResource.class);
	        return router;	
	        }

	@Override
	public String basePath() {
        return "/wm/quantum";
	}

}
