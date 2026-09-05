"use client";

import { useRef, useCallback, useEffect, useState } from "react";
import Map, {
  Marker,
  Popup,
  MapRef,
  MapLayerMouseEvent,
} from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import { useNewsStore } from "@/lib/newsStore";
import { CATEGORY_COLORS, NewsArticle } from "@/lib/types";
import { COUNTRY_BY_CODE } from "@/lib/countryFeeds";
import DayNightOverlay from "./DayNightOverlay";
import * as topojson from "topojson-client";
import type { Topology } from "topojson-specification";

// ISO 3166-1 numeric → alpha-2 mapping for countries in our feed system
const ISO_NUM_TO_ALPHA2: Record<string, string> = {
  "004":"AF","008":"AL","012":"DZ","020":"AD","024":"AO","028":"AG","032":"AR",
  "036":"AU","040":"AT","044":"BS","048":"BH","050":"BD","051":"AM","052":"BB",
  "056":"BE","064":"BT","068":"BO","070":"BA","072":"BW","076":"BR","084":"BZ",
  "090":"SB","096":"BN","100":"BG","104":"MM","108":"BI","112":"BY","116":"KH",
  "120":"CM","124":"CA","140":"CF","144":"LK","148":"TD","152":"CL","156":"CN",
  "158":"TW","170":"CO","174":"KM","178":"CG","180":"CD","188":"CR","191":"HR",
  "192":"CU","196":"CY","203":"CZ","204":"BJ","208":"DK","214":"DO","218":"EC",
  "222":"SV","226":"GQ","231":"ET","232":"ER","233":"EE","242":"FJ","246":"FI",
  "250":"FR","262":"DJ","266":"GA","268":"GE","270":"GM","275":"PS","276":"DE",
  "288":"GH","300":"GR","308":"GD","320":"GT","324":"GN","328":"GY","332":"HT",
  "340":"HN","344":"HK","348":"HU","352":"IS","356":"IN","360":"ID","364":"IR",
  "368":"IQ","372":"IE","376":"IL","380":"IT","384":"CI","388":"JM","392":"JP",
  "398":"KZ","400":"JO","404":"KE","408":"KP","410":"KR","414":"KW","417":"KG",
  "418":"LA","422":"LB","426":"LS","428":"LV","430":"LR","434":"LY","440":"LT",
  "442":"LU","450":"MG","454":"MW","458":"MY","462":"MV","466":"ML","470":"MT",
  "478":"MR","480":"MU","484":"MX","496":"MN","498":"MD","504":"MA","508":"MZ",
  "512":"OM","516":"NA","524":"NP","528":"NL","540":"NC","554":"NZ","558":"NI",
  "562":"NE","566":"NG","578":"NO","586":"PK","591":"PA","598":"PG","600":"PY",
  "604":"PE","608":"PH","616":"PL","620":"PT","630":"PR","634":"QA","642":"RO",
  "643":"RU","646":"RW","682":"SA","686":"SN","688":"RS","694":"SL","702":"SG",
  "703":"SK","704":"VN","705":"SI","706":"SO","710":"ZA","716":"ZW","724":"ES",
  "728":"SS","729":"SD","740":"SR","748":"SZ","752":"SE","756":"CH","760":"SY",
  "762":"TJ","764":"TH","768":"TG","780":"TT","784":"AE","788":"TN","792":"TR",
  "795":"TM","800":"UG","804":"UA","818":"EG","826":"GB","834":"TZ","840":"US",
  "854":"BF","858":"UY","860":"UZ","862":"VE","887":"YE","894":"ZM",
};

const DARK_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

// Check if a point is on the visible hemisphere
function isOnVisibleSide(
  dotLat: number,
  dotLng: number,
  centerLat: number,
  centerLng: number
): boolean {
  const toRad = Math.PI / 180;
  const dLng = (dotLng - centerLng) * toRad;
  const lat1 = centerLat * toRad;
  const lat2 = dotLat * toRad;
  // Cosine of angular distance on the sphere
  const cosAngle =
    Math.sin(lat1) * Math.sin(lat2) +
    Math.cos(lat1) * Math.cos(lat2) * Math.cos(dLng);
  // visible if angle < 90° (cosAngle > 0), with small margin for edge dots
  return cosAngle > -0.1;
}

function NewsDot({
  article,
  onClick,
  visible,
}: {
  article: NewsArticle;
  onClick: (a: NewsArticle) => void;
  visible: boolean;
}) {
  const color = CATEGORY_COLORS[article.category] || "#ffffff";
  const { setHoveredArticle } = useNewsStore();

  if (!visible) return null;

  return (
    <Marker
      latitude={article.lat}
      longitude={article.lng}
      anchor="center"
    >
      <div
        className="relative cursor-pointer group"
        onClick={() => onClick(article)}
        onMouseEnter={() => setHoveredArticle(article)}
        onMouseLeave={() => setHoveredArticle(null)}
      >
        {/* Invisible larger hit area for touch */}
        <div
          className="absolute z-20"
          style={{
            width: 32,
            height: 32,
            top: -8,
            left: -8,
          }}
        />
        {/* Pulse ring */}
        <div
          className="absolute inset-0 rounded-full animate-ping opacity-30"
          style={{
            backgroundColor: color,
            width: 28,
            height: 28,
            top: -6,
            left: -6,
          }}
        />
        {/* Glow */}
        <div
          className="absolute rounded-full blur-sm"
          style={{
            backgroundColor: color,
            opacity: 0.4,
            width: 24,
            height: 24,
            top: -4,
            left: -4,
          }}
        />
        {/* Dot */}
        <div
          className="rounded-full border border-white/30 relative z-10"
          style={{
            backgroundColor: color,
            width: 16,
            height: 16,
            boxShadow: `0 0 8px ${color}, 0 0 20px ${color}40`,
          }}
        />
      </div>
    </Marker>
  );
}

export default function GlobeScene() {
  const mapRef = useRef<MapRef>(null);
  const { filteredArticles, selectCountry, selectedCountry, countryArticles, pendingFlyTo, flyToVersion } = useNewsStore();
  const [popupArticle, setPopupArticle] = useState<NewsArticle | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapCenter, setMapCenter] = useState({ lat: 30, lng: 20 });
  const [mapZoom, setMapZoom] = useState(1.8);
  const dotClickedRef = useRef(false);

  const dots = (selectedCountry ? countryArticles : filteredArticles).slice(0, 100);

  const handleDotClick = useCallback((article: NewsArticle) => {
    dotClickedRef.current = true;
    setPopupArticle(article);
  }, []);

  const handleMapClick = useCallback(
    (e: MapLayerMouseEvent) => {
      // Skip if a news dot was just clicked
      if (dotClickedRef.current) {
        dotClickedRef.current = false;
        return;
      }

      if (!mapRef.current) return;
      const map = mapRef.current.getMap();

      // Query the invisible country fill layer for polygon hit-testing
      const features = map.queryRenderedFeatures(e.point, {
        layers: ["country-fills"],
      });

      if (features.length === 0) return;

      const feature = features[0];
      const numericCode = String(feature.properties?.iso_n3 || feature.id || "");
      const alpha2 = ISO_NUM_TO_ALPHA2[numericCode];
      if (!alpha2) return;

      const countryData = COUNTRY_BY_CODE.get(alpha2);
      if (!countryData) return;

      selectCountry(alpha2, countryData.name);
      setPopupArticle(null);
    },
    [selectCountry]
  );

  const isUserInteracting = useRef(false);
  const isFlyingTo = useRef(false);

  // React to pendingFlyTo from store (country selection, search, back)
  useEffect(() => {
    if (!pendingFlyTo || !mapRef.current) return;
    const map = mapRef.current.getMap();

    isFlyingTo.current = true;
    map.once("moveend", () => {
      isFlyingTo.current = false;
    });

    mapRef.current.flyTo({
      center: [pendingFlyTo.lng, pendingFlyTo.lat],
      zoom: pendingFlyTo.zoom,
      duration: 1500,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flyToVersion]);
  const rotationSpeed = 0.03; // degrees per frame

  // Load country polygons for click detection
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    const map = mapRef.current.getMap();
    if (map.getSource("countries")) return;

    fetch("/countries-110m.json")
      .then((r) => r.json())
      .then((topo: Topology) => {
        const geojson = topojson.feature(topo, topo.objects.countries);
        // Add iso_n3 property from feature id for lookup
        if ("features" in geojson) {
          for (const f of geojson.features) {
            f.properties = { ...f.properties, iso_n3: String(f.id) };
          }
        }
        if (map.getSource("countries")) return;
        map.addSource("countries", { type: "geojson", data: geojson });
        map.addLayer({
          id: "country-fills",
          type: "fill",
          source: "countries",
          paint: {
            "fill-color": "transparent",
            "fill-opacity": 0,
          },
        });
      });
  }, [mapLoaded]);

  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    const map = mapRef.current.getMap();
    try {
      map.setProjection({ type: "globe" });
    } catch {
      // globe projection not supported in this version
    }

    // Track center for visibility culling
    const updateCenter = () => {
      const c = map.getCenter();
      setMapCenter({ lat: c.lat, lng: c.lng });
      setMapZoom(map.getZoom());
    };
    map.on("move", updateCenter);

    // Auto-rotate the globe
    let animationId: number;

    const ROTATION_MAX_ZOOM = 3.5; // stop rotating when zoomed in past this

    const rotate = () => {
      if (!isUserInteracting.current && !isFlyingTo.current && mapRef.current) {
        const map = mapRef.current.getMap();
        if (map.getZoom() < ROTATION_MAX_ZOOM) {
          const center = map.getCenter();
          center.lng += rotationSpeed;
          map.setCenter(center);
        }
      }
      animationId = requestAnimationFrame(rotate);
    };

    // Pause rotation on user interaction
    map.on("mousedown", () => { isUserInteracting.current = true; });
    map.on("touchstart", () => { isUserInteracting.current = true; });
    map.on("mouseup", () => { isUserInteracting.current = false; });
    map.on("touchend", () => { isUserInteracting.current = false; });
    map.on("wheel", () => {
      isUserInteracting.current = true;
      // Resume after a short delay
      setTimeout(() => { isUserInteracting.current = false; }, 2000);
    });

    animationId = requestAnimationFrame(rotate);

    return () => {
      cancelAnimationFrame(animationId);
      map.off("move", updateCenter);
    };
  }, [mapLoaded]);

  // When zoomed in enough, all dots are visible (flat map mode)
  const useGlobeCulling = mapZoom < 5;

  return (
    <div className="absolute inset-0">
      <Map
        ref={mapRef}
        initialViewState={{
          longitude: 20,
          latitude: 30,
          zoom: 1.8,
        }}
        style={{ width: "100%", height: "100%" }}
        mapStyle={DARK_STYLE}
        attributionControl={false}
        onLoad={() => setMapLoaded(true)}
        onClick={handleMapClick}
        maxZoom={18}
        minZoom={1}
      >

        <DayNightOverlay />

        {dots.map((article) => (
          <NewsDot
            key={article.id}
            article={article}
            onClick={handleDotClick}
            visible={
              !useGlobeCulling ||
              isOnVisibleSide(article.lat, article.lng, mapCenter.lat, mapCenter.lng)
            }
          />
        ))}

        {popupArticle && (
          <Popup
            latitude={popupArticle.lat}
            longitude={popupArticle.lng}
            anchor="bottom"
            onClose={() => setPopupArticle(null)}
            closeButton={true}
            closeOnClick={false}
            className="news-popup"
          >
            <div className="bg-black/95 p-3 rounded-lg max-w-[280px] -m-[10px]">
              <p className="text-white text-xs font-semibold leading-tight">
                {popupArticle.title}
              </p>
              {popupArticle.snippet && (
                <p className="text-gray-400 text-[10px] mt-1.5 leading-relaxed line-clamp-2">
                  {popupArticle.snippet}
                </p>
              )}
              <div className="flex items-center justify-between mt-2">
                <span className="text-gray-500 text-[10px]">
                  {popupArticle.source}
                </span>
                <a
                  href={popupArticle.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 text-[10px] hover:text-blue-300"
                >
                  Read more →
                </a>
              </div>
            </div>
          </Popup>
        )}
      </Map>
    </div>
  );
}
