import React, { useEffect, useMemo, useRef } from 'react';
import { Box, Paper, Typography } from '@mui/material';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { MarketTransaction } from '../../../types/market';
import { PropertyType } from '../../../types/property';
import type { FeatureCollection, Point } from 'geojson';

type TransactionFeatureProperties = {
  price: number;
  psf?: number | null;
  propertyName: string;
  date: string;
  district?: string | null;
};

// You'll need to set your Mapbox access token
mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_ACCESS_TOKEN || '';

interface MarketHeatmapProps {
  transactions: MarketTransaction[];
  propertyType: PropertyType;
}

const MarketHeatmap: React.FC<MarketHeatmapProps> = ({
  transactions,
  propertyType
}) => {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const map = useRef<mapboxgl.Map | null>(null);

  const filteredTransactions = useMemo(
    () => transactions.filter(transaction => transaction.property_type === propertyType),
    [transactions, propertyType]
  );

  const featureCollection = useMemo<FeatureCollection<Point, TransactionFeatureProperties>>(() => {
    const singaporeBounds = {
      minLng: 103.6,
      maxLng: 104.0,
      minLat: 1.2,
      maxLat: 1.5
    };

    return {
      type: 'FeatureCollection',
      features: filteredTransactions.map(transaction => {
        const lng = singaporeBounds.minLng + Math.random() * (singaporeBounds.maxLng - singaporeBounds.minLng);
        const lat = singaporeBounds.minLat + Math.random() * (singaporeBounds.maxLat - singaporeBounds.minLat);

        return {
          type: 'Feature' as const,
          geometry: {
            type: 'Point',
            coordinates: [lng, lat]
          },
          properties: {
            price: transaction.sale_price,
            psf: transaction.psf_price ?? null,
            propertyName: transaction.property_name,
            date: new Date(transaction.transaction_date).toLocaleDateString(),
            district: transaction.district ?? null
          }
        };
      })
    };
  }, [filteredTransactions]);

  const featureCollectionRef = useRef(featureCollection);
  featureCollectionRef.current = featureCollection;

  useEffect(() => {
    if (!mapContainer.current || !mapboxgl.accessToken) return;

    // Initialize map centered on Singapore
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v10',
      center: [103.8198, 1.3521],
      zoom: 11
    });

    map.current.on('load', () => {
      if (!map.current) return;

      // Add heatmap layer
      map.current.addSource('transactions', {
        type: 'geojson',
        data: featureCollectionRef.current
      });

      // Add heatmap layer
      map.current.addLayer({
        id: 'transaction-heat',
        type: 'heatmap',
        source: 'transactions',
        paint: {
          // Increase weight as diameter breast height increases
          'heatmap-weight': [
            'interpolate',
            ['linear'],
            ['get', 'price'],
            0, 0,
            1000000, 1
          ],
          // Increase intensity as zoom level increases
          'heatmap-intensity': [
            'interpolate',
            ['linear'],
            ['zoom'],
            0, 1,
            15, 3
          ],
          // Use sequential color palette to paint heat map
          'heatmap-color': [
            'interpolate',
            ['linear'],
            ['heatmap-density'],
            0, 'rgba(0,0,0,0)',
            0.2, 'rgb(50,100,200)',
            0.4, 'rgb(50,150,200)',
            0.6, 'rgb(50,200,150)',
            0.8, 'rgb(200,200,50)',
            1, 'rgb(200,100,50)'
          ],
          // Adjust radius based on zoom
          'heatmap-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            0, 2,
            15, 20
          ],
          // Decrease opacity to see through to streets below
          'heatmap-opacity': 0.7
        }
      });

      // Add points layer for higher zoom levels
      map.current.addLayer({
        id: 'transaction-points',
        type: 'circle',
        source: 'transactions',
        minzoom: 14,
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            14, ['interpolate', ['linear'], ['get', 'price'], 0, 5, 10000000, 15],
            22, ['interpolate', ['linear'], ['get', 'price'], 0, 20, 10000000, 50]
          ],
          'circle-color': [
            'interpolate',
            ['linear'],
            ['get', 'price'],
            0, 'rgb(50,100,200)',
            5000000, 'rgb(200,200,50)',
            10000000, 'rgb(200,100,50)'
          ],
          'circle-stroke-color': 'white',
          'circle-stroke-width': 1,
          'circle-opacity': [
            'interpolate',
            ['linear'],
            ['zoom'],
            14, 0,
            15, 1
          ]
        }
      });

      // Add popups
      map.current.on('click', 'transaction-points', (e) => {
        if (!map.current || !e.features?.length) return;

        const feature = e.features[0];
        if (feature.geometry?.type !== 'Point') return;

        const coordinates = [...feature.geometry.coordinates] as [number, number];
        const properties = feature.properties as TransactionFeatureProperties | undefined;
        if (!properties) return;

        const formattedPsf =
          properties.psf !== null && properties.psf !== undefined
            ? new Intl.NumberFormat('en-SG').format(properties.psf)
            : 'N/A';

        new mapboxgl.Popup()
          .setLngLat(coordinates)
          .setHTML(`
            <div>
              <strong>${properties.propertyName}</strong><br/>
              Price: $${new Intl.NumberFormat('en-SG').format(properties.price)}<br/>
              PSF: $${formattedPsf}<br/>
              Date: ${properties.date}
            </div>
          `)
          .addTo(map.current);
      });

      // Change cursor on hover
      map.current.on('mouseenter', 'transaction-points', () => {
        if (map.current) map.current.getCanvas().style.cursor = 'pointer';
      });

      map.current.on('mouseleave', 'transaction-points', () => {
        if (map.current) map.current.getCanvas().style.cursor = '';
      });
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;

    const source = map.current.getSource('transactions');
    if (source && 'setData' in source) {
      (source as mapboxgl.GeoJSONSource).setData(featureCollection);
    }
  }, [featureCollection]);

  if (!mapboxgl.accessToken) {
    return (
      <Paper sx={{ p: 3, height: 500 }}>
        <Typography variant="body1" color="textSecondary" align="center">
          Map requires Mapbox access token. Set REACT_APP_MAPBOX_ACCESS_TOKEN in environment.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2, height: 500 }}>
      <Typography variant="h6" gutterBottom>
        Transaction Heatmap
      </Typography>
      <Box ref={mapContainer} sx={{ height: 450, borderRadius: 1, overflow: 'hidden' }} />
    </Paper>
  );
};

export default MarketHeatmap;